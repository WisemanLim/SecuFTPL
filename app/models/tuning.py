"""secuftpl — 튜닝 잡·평가 결과 테이블 (PRD E3, §7.5)."""
from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class TuningJobRow(Base):
    """QLoRA SFT 잡. 실행은 worker(GPU) — 코어는 오케스트레이션·플랜·상태만.
    status: queued → running → succeeded / failed."""

    __tablename__ = "tuning_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    model_id: Mapped[str] = mapped_column(String(256), index=True)
    dataset_version: Mapped[str] = mapped_column(String(64))
    record_count: Mapped[int] = mapped_column(default=0)  # 스냅샷 시점 approved 수
    status: Mapped[str] = mapped_column(String(16), default="queued", index=True)
    progress_pct: Mapped[float] = mapped_column(Float, default=0.0)  # 0~100 (running 진행률)
    current_step: Mapped[int] = mapped_column(default=0)
    total_steps: Mapped[int] = mapped_column(default=0)
    adapter_uri: Mapped[str | None] = mapped_column(String(512), default=None)
    error: Mapped[str | None] = mapped_column(String(512), default=None)
    triggered_by: Mapped[str] = mapped_column(String(16), default="manual")  # manual | batch
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class EvalResultRow(Base):
    """리더보드 행 — 모델×데이터셋 버전 쌍당 평가 지표(영구 보존, §7.7)."""

    __tablename__ = "eval_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    model_id: Mapped[str] = mapped_column(String(256), index=True)
    dataset_version: Mapped[str] = mapped_column(String(64), index=True)
    job_id: Mapped[str | None] = mapped_column(String(64), default=None)  # None=무튜닝 베이스라인
    cases: Mapped[int] = mapped_column(default=0)
    json_valid_rate: Mapped[float] = mapped_column(Float, default=0.0)
    severity_accuracy: Mapped[float] = mapped_column(Float, default=0.0)
    exact_match_rate: Mapped[float] = mapped_column(Float, default=0.0)
    attack_precision: Mapped[float] = mapped_column(Float, default=0.0)
    attack_recall: Mapped[float] = mapped_column(Float, default=0.0)
    attack_f1: Mapped[float] = mapped_column(Float, default=0.0)
    extra: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
