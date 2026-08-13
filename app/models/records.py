"""secuftpl — 데이터셋 레코드·가명화 매핑 테이블 (PRD §7.3 ⑤·⑨)."""
from datetime import datetime

from sqlalchemy import JSON, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class DatasetRecordRow(Base):
    """검수 큐에 적재된 canonical 레코드 (게이트 통과 후 pending → approve/reject)."""

    __tablename__ = "dataset_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    record_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    payload: Mapped[dict] = mapped_column(JSON)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    review_state: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    quality_grade: Mapped[str] = mapped_column(String(16), default="silver")
    lineage_of: Mapped[str | None] = mapped_column(String(128), default=None, index=True)
    reviewer: Mapped[str | None] = mapped_column(String(64), default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class PseudonymRow(Base):
    """가명화 안정 토큰 매핑 — 전역 일관 치환(동일 원문=동일 토큰). 접근통제 대상(COMPLIANCE)."""

    __tablename__ = "pseudonym_map"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(512), unique=True, index=True)  # "<KIND>:<원문>"
    kind: Mapped[str] = mapped_column(String(32), index=True)
    token: Mapped[str] = mapped_column(String(64))
