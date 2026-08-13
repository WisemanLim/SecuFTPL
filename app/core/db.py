"""secuftpl — DB 세션/엔진 (SQLAlchemy 2.x, DATABASE_URL 주도)."""
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


_connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    # 1차: create_all. 스키마 진화 시 alembic migration 으로 전환.
    from app.models import records, registry, tuning  # noqa: F401 — 테이블 등록
    from app.services import (  # noqa: F401 — batch_runs·job_events 테이블 등록
        batch,
        trainer,
    )

    Base.metadata.create_all(engine)
