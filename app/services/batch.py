"""secuftpl — 야간 배치 파인튜닝 자동화 (PRD F5·§7.5·§7.9, E6).

흐름: 트리거 판정(FT_TRIGGER_MODE) → 데이터셋 스냅샷(승인분) → pinned 모델별 튜닝 잡 생성
→ (worker 학습·평가 후) 평가 게이트 → 통과 시 배포 승인, 미통과 시 차단·이전 버전 유지.
스케줄 자체(cron)는 ops 가 담당 — 이 서비스는 배치 1회 실행의 결정·기록만.
전 과정 감사 기록(batch_runs, append-only 원칙 — 갱신은 상태 전이만).
"""
import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, String, func, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.core.config import settings
from app.core.db import Base
from app.models.records import DatasetRecordRow
from app.models.registry import ModelRow
from app.models.tuning import EvalResultRow
from app.services.tuning import create_job

# 평가 게이트 하한 (PRD §5 — 기준선 확정 전 가정값, env/추후 조정)
GATE_MIN = {"json_valid_rate": 0.98, "severity_accuracy": 0.85}


class BatchRunRow(Base):
    __tablename__ = "batch_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    trigger_mode: Mapped[str] = mapped_column(String(16))
    trigger_detail: Mapped[dict] = mapped_column(JSON, default=dict)
    dataset_version: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(24), index=True)  # skipped_below_threshold | jobs_created
    jobs: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


def _approved_stats(db: Session) -> tuple[int, int]:
    rows = db.scalars(select(DatasetRecordRow).where(
        DatasetRecordRow.review_state == "approved")).all()
    records = len(rows)
    # 토큰 근사: 공백 분리 어절 수 (실 토크나이저는 worker 에서 — 트리거 판정용 근사)
    tokens = sum(
        len(m["content"].split())
        for r in rows for m in r.payload.get("messages", [])
    )
    return records, tokens


def should_run(db: Session, mode: str | None = None) -> tuple[bool, dict]:
    """트리거 판정 (PRD §7.9): schedule=항상 실행(스케줄러가 시점 결정),
    record_count/token_count=임계 도달 시만."""
    mode = mode or settings.ft_trigger_mode
    records, tokens = _approved_stats(db)
    detail = {"mode": mode, "approved_records": records, "approx_tokens": tokens}
    if mode == "schedule":
        return records > 0, detail  # 학습할 데이터가 아예 없으면 스킵
    if mode == "record_count":
        detail["threshold"] = settings.ft_trigger_record_threshold
        return records >= settings.ft_trigger_record_threshold, detail
    if mode == "token_count":
        detail["threshold"] = settings.ft_trigger_token_threshold
        return tokens >= settings.ft_trigger_token_threshold, detail
    raise ValueError(f"invalid trigger mode: {mode}")


def evaluation_gate(db: Session, model_id: str, dataset_version: str) -> dict:
    """배포 게이트: 최신 지표가 하한 충족 + 이전 결과 대비 회귀 없음(attack_f1)."""
    rows = db.scalars(select(EvalResultRow).where(
        EvalResultRow.model_id == model_id).order_by(EvalResultRow.id)).all()
    candidates = [r for r in rows if r.dataset_version == dataset_version]
    if not candidates:
        return {"passed": False, "reason": f"no evaluation result for {dataset_version}"}
    latest = candidates[-1]
    for metric, minimum in GATE_MIN.items():
        if getattr(latest, metric) < minimum:
            return {"passed": False, "reason": f"{metric} {getattr(latest, metric):.3f} < {minimum}"}
    previous = [r for r in rows if r.id != latest.id]
    if previous and latest.attack_f1 < max(r.attack_f1 for r in previous):
        return {"passed": False,
                "reason": f"regression: attack_f1 {latest.attack_f1:.3f} < best previous"}
    return {"passed": True, "reason": "gate passed", "attack_f1": latest.attack_f1}


def run_batch(db: Session, mode: str | None = None, triggered_by: str = "batch") -> dict:
    """배치 1회 실행: 트리거 판정 → 스냅샷 버전 → pinned 모델별 잡 생성."""
    ok, detail = should_run(db, mode)
    run_id = f"batch-{uuid.uuid4().hex[:12]}"
    snapshot = f"snap-{datetime.now(UTC).strftime('%Y%m%d')}-{run_id[-4:]}"
    if not ok:
        run = BatchRunRow(run_id=run_id, trigger_mode=detail["mode"], trigger_detail=detail,
                          dataset_version=snapshot, status="skipped_below_threshold", jobs=[])
        db.add(run)
        db.commit()
        return {"run_id": run_id, "status": run.status, "detail": detail, "jobs": []}
    pinned = db.scalars(select(ModelRow).where(ModelRow.status == "pinned")).all()
    if not pinned:
        run = BatchRunRow(run_id=run_id, trigger_mode=detail["mode"], trigger_detail=detail,
                          dataset_version=snapshot, status="skipped_no_pinned_model", jobs=[])
        db.add(run)
        db.commit()
        return {"run_id": run_id, "status": run.status, "detail": detail, "jobs": []}
    jobs = [create_job(db, m.model_id, snapshot, triggered_by=triggered_by).job_id for m in pinned]
    run = BatchRunRow(run_id=run_id, trigger_mode=detail["mode"], trigger_detail=detail,
                      dataset_version=snapshot, status="jobs_created", jobs=jobs)
    db.add(run)
    db.commit()
    from app.services.trainer import admit_or_queue

    for job_id in jobs:  # 리소스 상한 내에서 즉시 시작, 초과 시 큐잉(F9)
        admit_or_queue(job_id)
    return {"run_id": run_id, "status": run.status, "dataset_version": snapshot,
            "detail": detail, "jobs": jobs}
