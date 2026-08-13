"""secuftpl — FastAPI entrypoint (정적 템플릿 / static scaffold)."""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from app.api.batch import router as batch_router
from app.api.datasets import router as datasets_router
from app.api.feedback import router as feedback_router
from app.api.rag import router as rag_router
from app.api.records import router as records_router
from app.api.registry import router as registry_router
from app.api.tuning import router as tuning_router
from app.core.config import settings
from app.core.db import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.include_router(datasets_router)
app.include_router(records_router)
app.include_router(registry_router)
app.include_router(tuning_router)
app.include_router(feedback_router)
app.include_router(batch_router)
app.include_router(rag_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.env}


@app.get("/supervisor", include_in_schema=False)
def supervisor() -> FileResponse:
    """Supervisor 파이프라인 시험 UI (PRD F7 — 로그인 없음, 내부망 전용)."""
    return FileResponse(Path(__file__).parent / "web" / "supervisor.html")
