"""secuftpl — 베이스모델 레지스트리 테이블 (PRD F2, E2)."""
from datetime import datetime

from sqlalchemy import DateTime, Float, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class ModelRow(Base):
    """레지스트리 항목. status: registered(시드) → pinned(revision 고정, 에어갭 반입 가능)
    / candidate(이벤트 감지 후보, 벤치마크 대기) / retired."""

    __tablename__ = "model_registry"

    id: Mapped[int] = mapped_column(primary_key=True)
    model_id: Mapped[str] = mapped_column(String(256), unique=True, index=True)
    tier: Mapped[str] = mapped_column(String(8))  # pilot | core | all
    role: Mapped[str] = mapped_column(String(32), default="gen")
    notes: Mapped[str] = mapped_column(String(512), default="")
    family: Mapped[str] = mapped_column(String(64), index=True)
    param_size_b: Mapped[float | None] = mapped_column(Float, default=None)
    license: Mapped[str | None] = mapped_column(String(64), default=None)  # 모델카드 확인 후 기입
    revision: Mapped[str | None] = mapped_column(String(64), default=None)  # pin 시 커밋 해시
    status: Mapped[str] = mapped_column(String(16), default="registered", index=True)
    source: Mapped[str] = mapped_column(String(16), default="seed")  # seed | event
    matched_to: Mapped[str | None] = mapped_column(String(256), default=None)  # 유사 판정 근거 모델
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
