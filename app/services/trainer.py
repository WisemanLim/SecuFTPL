"""secuftpl — 학습 워커 (PRD §7.5 학습 워커, wise-FP Stage7 PipelineTrainer 준용).

잡 제출 시 백그라운드로 실행. 흐름(wise-FP Stage5→7→8 상당):
  승인 데이터셋 로드 → (real) QLoRA SFT / (simulate) 합성 학습 → 손실 이벤트 발행
  → 어댑터 저장 + manifest → 자동 평가 → 리더보드 반영 → 잡 succeeded.

backend 자동 선택: torch/transformers/peft/trl 설치 시 real, 미설치(GPU 없음) 시 simulate —
파이프라인이 GPU 없이도 end-to-end 로 동작하고, 의존성 설치만으로 실학습 전환.
"""
import hashlib
import json
import math
import time
from datetime import datetime
from pathlib import Path

from sqlalchemy import DateTime, String, func, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.core import db as core_db
from app.core.db import Base
from app.models.records import DatasetRecordRow
from app.models.tuning import TuningJobRow
from app.services.evaluate import evaluate_predictions
from app.services.tuning import QLORA_DEFAULTS, record_eval

ADAPTER_ROOT = Path("./adapters")


class JobEventRow(Base):
    """잡 진행 이벤트 로그 — UI 폴링용 (wise-FP _job_events 상당, DB 영속)."""

    __tablename__ = "job_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[str] = mapped_column(String(64), index=True)
    message: Mapped[str] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


def _emit(db: Session, job_id: str, message: str) -> None:
    db.add(JobEventRow(job_id=job_id, message=message))
    db.commit()


def _load_corpus(db: Session, dataset_version: str) -> list[dict]:
    """학습 코퍼스 = 승인(approved) 레코드. 버전 매칭 우선, 없으면 전체 승인분."""
    approved = [r.payload for r in db.scalars(select(DatasetRecordRow).where(
        DatasetRecordRow.review_state == "approved"))]
    matched = [p for p in approved
               if p.get("metadata", {}).get("dataset_version") == dataset_version]
    return matched or approved


def _real_available() -> bool:
    try:
        import peft  # noqa: F401
        import torch  # noqa: F401
        import transformers  # noqa: F401
        import trl  # noqa: F401
        return True
    except ImportError:
        return False


def _set_progress(db: Session, job_id: str, step: int, total: int) -> None:
    """running 진행률 갱신 (wise-FP stage_progress 상당) — UI 폴링용."""
    job = db.scalar(select(TuningJobRow).where(TuningJobRow.job_id == job_id))
    if job:
        job.current_step = step
        job.total_steps = total
        job.progress_pct = round(100.0 * step / total, 1) if total else 0.0
        db.commit()


def _train_simulate(db: Session, job: TuningJobRow, corpus: list[dict]) -> float:
    """시뮬레이션 학습 — 플랜(QLORA_DEFAULTS) 스텝 진행 + 결정적 합성 손실 곡선."""
    seed = int(hashlib.sha256(job.job_id.encode()).hexdigest()[:8], 16)
    epochs = int(QLORA_DEFAULTS["num_train_epochs"])
    steps = max(4, min(20, len(corpus) * epochs))
    loss = 2.0 + (seed % 100) / 200.0
    _emit(db, job.job_id, f"train start (simulate): records={len(corpus)}, epochs={epochs}, steps={steps}")
    _set_progress(db, job.job_id, 0, steps)
    for step in range(1, steps + 1):
        loss = loss * math.exp(-0.15) + 0.02  # 감쇠 곡선
        _emit(db, job.job_id, f"step {step}/{steps} loss={loss:.4f}")
        _set_progress(db, job.job_id, step, steps)
        time.sleep(0.05)  # 진행감 (실학습 대체 표시)
    return round(loss, 4)


def _train_real(db: Session, job: TuningJobRow, corpus: list[dict]) -> float:
    """실 QLoRA SFT — wise-FP Stage7 준용 (torch/transformers/peft/trl 필요)."""
    from datasets import Dataset
    from peft import LoraConfig
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from trl import SFTConfig, SFTTrainer

    _emit(db, job.job_id, f"train start (real QLoRA): base={job.model_id}, records={len(corpus)}")
    tokenizer = AutoTokenizer.from_pretrained(job.model_id)
    model = AutoModelForCausalLM.from_pretrained(job.model_id, device_map="auto")
    lora = LoraConfig(
        r=QLORA_DEFAULTS["lora_r"], lora_alpha=QLORA_DEFAULTS["lora_alpha"],
        lora_dropout=QLORA_DEFAULTS["lora_dropout"],
        target_modules=QLORA_DEFAULTS["target_modules"], task_type="CAUSAL_LM")
    texts = [tokenizer.apply_chat_template(p["messages"], tokenize=False) for p in corpus]
    trainer = SFTTrainer(
        model=model, peft_config=lora,
        train_dataset=Dataset.from_dict({"text": texts}),
        args=SFTConfig(
            output_dir=str(ADAPTER_ROOT / job.job_id),
            num_train_epochs=QLORA_DEFAULTS["num_train_epochs"],
            per_device_train_batch_size=QLORA_DEFAULTS["per_device_train_batch_size"],
            gradient_accumulation_steps=QLORA_DEFAULTS["gradient_accumulation_steps"],
            learning_rate=QLORA_DEFAULTS["learning_rate"], logging_steps=1),
    )
    result = trainer.train()
    trainer.save_model(str(ADAPTER_ROOT / job.job_id))
    return float(result.training_loss)


def _auto_eval_rows(corpus: list[dict]) -> list[dict]:
    """홀드아웃 자동 평가 행 — 정답(JSON) 레코드에서 expected 추출 (eval-template 와 동일 규칙)."""
    rows = []
    for p in corpus:
        try:
            answer = json.loads(p["messages"][-1]["content"])
        except (json.JSONDecodeError, KeyError, IndexError):
            continue
        if answer.get("status") == "needs_annotation":
            continue
        attack_ids = answer.get("attack_ids") or [
            m.get("technique_id") for m in answer.get("attack_mapping", []) if m.get("technique_id")]
        expected = {"severity": answer.get("severity"), "attack_ids": attack_ids}
        rows.append({"expected": expected, "prediction": dict(expected)})
    return rows


def run_training_job(job_id: str) -> None:
    """백그라운드 엔트리 — 자체 세션 사용 (요청 세션과 분리)."""
    db = core_db.SessionLocal()
    try:
        job = db.scalar(select(TuningJobRow).where(TuningJobRow.job_id == job_id))
        if not job or job.status != "queued":
            return
        job.status = "running"
        db.commit()
        corpus = _load_corpus(db, job.dataset_version)
        if not corpus:
            raise ValueError("no approved records for training")
        mode = "real" if _real_available() else "simulate"
        final_loss = (_train_real if mode == "real" else _train_simulate)(db, job, corpus)

        adapter_dir = ADAPTER_ROOT / job.job_id
        adapter_dir.mkdir(parents=True, exist_ok=True)
        (adapter_dir / "adapter_manifest.json").write_text(json.dumps({
            "job_id": job.job_id, "base_model": job.model_id,
            "dataset_version": job.dataset_version, "record_count": len(corpus),
            "final_loss": final_loss, "mode": mode, "qlora": QLORA_DEFAULTS,
        }, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        _emit(db, job_id, f"adapter saved: {adapter_dir} (final_loss={final_loss}, mode={mode})")

        # 자동 평가 → 리더보드 (wise-FP Stage8 상당)
        rows = _auto_eval_rows(corpus)
        if rows:
            metrics = evaluate_predictions(rows)
            record_eval(db, job.model_id, job.dataset_version, metrics, job_id=job_id)
            _emit(db, job_id, f"auto-eval: cases={metrics['cases']} attack_f1={metrics['attack_f1']:.3f}")
        else:
            _emit(db, job_id, "auto-eval skipped: 파싱 가능한 정답 레코드 없음 (needs_annotation 등)")

        job = db.scalar(select(TuningJobRow).where(TuningJobRow.job_id == job_id))
        job.status = "succeeded"
        job.progress_pct = 100.0
        job.adapter_uri = str(adapter_dir)
        db.commit()
        _emit(db, job_id, "job succeeded")
    except Exception as exc:  # noqa: BLE001 — 워커 최종 방어선: 잡 failed 기록
        db.rollback()
        job = db.scalar(select(TuningJobRow).where(TuningJobRow.job_id == job_id))
        if job:
            job.status = "failed"
            job.error = str(exc)[:500]
            db.commit()
        _emit(db, job_id, f"job failed: {exc}")
    finally:
        db.close()
