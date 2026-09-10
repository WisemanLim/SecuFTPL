"""secuftpl — 튜닝 잡 오케스트레이션·학습 플랜·리더보드 (PRD E3, §7.5).

실학습(QLoRA)은 GPU worker 전제 — 코어는 잡 상태·학습 플랜(YAML) 생성·평가 반영만 담당
(download-plan 과 동일 원칙: 명령/설정 생성만, 실행 없음).
QLoRA 기본값 근거: .docs/Perplexity-보안분야 LLM 모델 생성.md §QLoRA 비용 최적화.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.records import DatasetRecordRow
from app.models.registry import ModelRow
from app.models.tuning import EvalResultRow, TuningJobRow

# 문서 권장 출발 구성 (7B/14B QLoRA)
QLORA_DEFAULTS = {
    "load_in_4bit": True,
    "bnb_4bit_quant_type": "nf4",
    "bnb_4bit_compute_dtype": "bfloat16",
    "lora_r": 16,
    "lora_alpha": 32,
    "lora_dropout": 0.05,
    "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj"],
    "learning_rate": 2.0e-4,
    "num_train_epochs": 2,
    "per_device_train_batch_size": 1,
    "gradient_accumulation_steps": 16,
    "gradient_checkpointing": True,
    "max_seq_length": 2048,
}


def create_job(db: Session, model_id: str, dataset_version: str,
               triggered_by: str = "manual",
               max_gpu: int | None = None, max_vram_gb: int | None = None,
               continual_from_job_id: str | None = None) -> TuningJobRow:
    """튜닝 잡 생성. 모델은 레지스트리 등록 필수, 데이터셋은 approved 레코드가 최소 임계값
    이상이어야 함(F1·F9 튜닝 시작 게이트, PRD §7.5·DATASET_MIN_RECORDS).
    `continual_from_job_id` 지정 시 해당(succeeded) 잡의 어댑터를 이어학습 기준으로 삼는다
    (F10 RAG 추가학습·모델 업그레이드, §7.13 — 실 이어학습은 worker 몫, 코어는 참조만 기록)."""
    model = db.scalar(select(ModelRow).where(ModelRow.model_id == model_id))
    if not model:
        raise ValueError(f"model not registered: {model_id}")
    if model.status not in ("downloaded", "pinned"):
        raise ValueError(
            f"model '{model_id}' 상태 '{model.status}' — 학습하려면 먼저 다운로드(downloaded/pinned) 필요")
    if continual_from_job_id:
        base_job = db.scalar(select(TuningJobRow).where(
            TuningJobRow.job_id == continual_from_job_id))
        if not base_job:
            raise ValueError(f"continual_from_job_id not found: {continual_from_job_id}")
        if base_job.status != "succeeded":
            raise ValueError(
                f"continual_from_job_id '{continual_from_job_id}' 상태 '{base_job.status}' — "
                "succeeded 잡의 어댑터만 이어학습 기준으로 사용 가능")
    approved = db.scalars(select(DatasetRecordRow).where(
        DatasetRecordRow.review_state == "approved")).all()
    if not approved:
        raise ValueError("no approved records — 검수 승인된 레코드가 없어 잡을 만들 수 없음")
    minimum = settings.dataset_min_records
    if len(approved) < minimum:
        raise ValueError(
            f"approved records {len(approved)}건 < 최소 {minimum}건 — "
            f"승인 레코드를 {minimum}건 이상 확보한 뒤 튜닝 잡을 제출하세요 (DATASET_MIN_RECORDS)")
    job = TuningJobRow(
        job_id=f"ft-{uuid.uuid4().hex[:12]}", model_id=model_id,
        dataset_version=dataset_version, record_count=len(approved),
        triggered_by=triggered_by,
        max_gpu=max_gpu if max_gpu is not None else settings.job_max_gpu,
        max_vram_gb=max_vram_gb if max_vram_gb is not None else settings.job_max_vram_gb,
        continual_from_job_id=continual_from_job_id,
    )
    db.add(job)
    db.commit()
    return job


LORA_VARIANTS = ("lora", "rslora", "dora")


def train_plan(job: TuningJobRow, lora_variant: str = "lora") -> str:
    """worker(GPU) 에서 실행할 QLoRA SFT 플랜(YAML) — 생성만, 실행 없음.
    lora_variant(PRD F19, Survey §2.1): rslora=α/√r 스케일링, dora=크기·방향 분해 (HF PEFT 플래그)."""
    if lora_variant not in LORA_VARIANTS:
        raise ValueError(f"invalid lora_variant: {lora_variant} (지원: {LORA_VARIANTS})")
    lines = [
        f"# secuftpl train plan — {job.job_id}",
        "# worker 실행: uv run python -m worker.train --config <this file>",
        f"base_model: {job.model_id}",
        f"dataset_version: {job.dataset_version}",
        f"record_count: {job.record_count}",
        "dataset_format: sft-messages   # canonical JSONL (approved only)",
        f"output_dir: ./adapters/{job.job_id}",
        "method: qlora",
    ]
    for k, v in QLORA_DEFAULTS.items():
        lines.append(f"{k}: {v}")
    lines.append(f"lora_variant: {lora_variant}")
    if lora_variant == "rslora":
        lines.append("use_rslora: true              # 고랭크 안정화 (arXiv:2312.03732)")
    elif lora_variant == "dora":
        lines.append("use_dora: true                # 크기·방향 분해 (arXiv:2402.09353)")
    lines += [
        "eval_after_train: true          # 평가 게이트 — 통과 시에만 배포 (PRD §7.5)",
        "report_to: POST /api/v1/tuning/jobs/{job_id}/complete",
    ]
    return "\n".join(lines)


def complete_job(db: Session, job_id: str, status: str, adapter_uri: str | None = None,
                 metrics: dict | None = None, error: str | None = None) -> TuningJobRow:
    """worker 콜백: 잡 종료 처리 + 지표를 리더보드에 반영."""
    job = db.scalar(select(TuningJobRow).where(TuningJobRow.job_id == job_id))
    if not job:
        raise ValueError(f"job not found: {job_id}")
    if job.status in ("succeeded", "failed"):
        raise ValueError(f"job already finished: {job.status}")
    job.status = status
    job.adapter_uri = adapter_uri
    job.error = error
    if status == "succeeded" and metrics:
        record_eval(db, job.model_id, job.dataset_version, metrics, job_id=job_id)
    db.commit()
    return job


def record_eval(db: Session, model_id: str, dataset_version: str, metrics: dict,
                job_id: str | None = None) -> EvalResultRow:
    """평가 지표 리더보드 반영 (job_id=None 이면 무튜닝 베이스라인)."""
    known = {c.name for c in EvalResultRow.__table__.columns}
    row = EvalResultRow(
        model_id=model_id, dataset_version=dataset_version, job_id=job_id,
        **{k: v for k, v in metrics.items() if k in known and k not in ("id", "model_id", "dataset_version", "job_id")},
        extra={k: v for k, v in metrics.items() if k not in known},
    )
    db.add(row)
    db.commit()
    return row


def leaderboard(db: Session, dataset_version: str | None = None,
                sort_by: str = "attack_f1") -> list[dict]:
    """모델 간 비교 리더보드 — 기본 attack_f1 내림차순."""
    q = select(EvalResultRow)
    if dataset_version:
        q = q.where(EvalResultRow.dataset_version == dataset_version)
    rows = db.scalars(q).all()
    items = [{
        "model_id": r.model_id, "dataset_version": r.dataset_version,
        "job_id": r.job_id, "baseline": r.job_id is None, "cases": r.cases,
        "json_valid_rate": r.json_valid_rate, "severity_accuracy": r.severity_accuracy,
        "exact_match_rate": r.exact_match_rate, "attack_f1": r.attack_f1,
        "attack_precision": r.attack_precision, "attack_recall": r.attack_recall,
    } for r in rows]
    return sorted(items, key=lambda x: x.get(sort_by, 0.0), reverse=True)
