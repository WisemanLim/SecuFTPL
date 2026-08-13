"""secuftpl — RAG 기반 추가학습·모델 업그레이드 API (PRD F10·§7.13, E10).

흐름: ① RAG 코퍼스(텍스트/문서) → 합성 QA 레코드 → 기존 게이트/검수 큐 편입(F3 채널·§7.3 재사용,
게이트 무우회 금지) → ② 검수 승인(`/api/v1/records/{id}/review`, 기존 엔드포인트) →
③ 승인 데이터셋으로 continual fine-tuning 잡 제출(F1 튜닝 오케스트레이션 재사용).
"""
from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.records import IngestRequest, ingest
from app.core.db import get_db
from app.services.tuning import create_job

router = APIRouter(prefix="/api/v1/rag", tags=["rag"])
DbSession = Annotated[Session, Depends(get_db)]


class DocumentItem(BaseModel):
    title: str = Field(min_length=1)
    text: str = Field(min_length=1)


class SynthesizeRequest(BaseModel):
    documents: list[DocumentItem] = Field(min_length=1)
    task_type: str = "alert_triage"
    dataset_version: str = "v0.1.0"
    chunk_size: int = Field(default=800, ge=200, le=4000)


@router.post("/synthesize")
def synthesize(req: SynthesizeRequest, db: DbSession) -> dict:
    """RAG 코퍼스(텍스트) → 합성 QA 레코드 생성 → 검수 큐 편입. 승인은 기존
    `/api/v1/records/{record_id}/review` 로 별도 수행(게이트 무우회 원칙 유지)."""
    from app.services.rag_synth import chunk_text, synthesize_records

    records = []
    for doc in req.documents:
        chunks = chunk_text(doc.text, req.chunk_size)
        records.extend(synthesize_records(chunks, req.task_type, req.dataset_version, doc.title))
    if not records:
        raise HTTPException(status_code=422, detail="no synthesizable text in documents")
    result = ingest(IngestRequest(records=records), db)
    return {"documents": len(req.documents), "chunks": len(records), "ingest": result}


@router.post("/upload")
async def synthesize_upload(
    db: DbSession,
    files: Annotated[list[UploadFile], File(description="RAG 코퍼스 문서 (PDF/DOCX/TXT/MD/HTML, 복수)")],
    task_type: Annotated[str, Form()] = "alert_triage",
    dataset_version: Annotated[str, Form()] = "v0.1.0",
    chunk_size: Annotated[int, Form()] = 800,
) -> dict:
    """문서 파일 업로드 → 합성 레코드 (F3 문서 수집 채널의 텍스트 추출 재사용)."""
    from app.services.rag_synth import synthesize_from_document

    records: list[dict] = []
    reports = []
    for f in files:
        try:
            recs = synthesize_from_document(await f.read(), f.filename or "doc.txt",
                                            task_type, dataset_version, chunk_size)
            records.extend(recs)
            reports.append({"file": f.filename, "chunks": len(recs), "status": "ok"})
        except ValueError as exc:
            reports.append({"file": f.filename, "chunks": 0, "status": f"error: {exc}"})
    if not records:
        raise HTTPException(status_code=422, detail={"message": "no synthesizable text", "files": reports})
    return {"files": reports, "ingest": ingest(IngestRequest(records=records), db)}


class UpgradeRequest(BaseModel):
    model_id: str
    dataset_version: str
    continual_from_job_id: str | None = None  # 이어학습 기준 어댑터(선택, succeeded 잡만)
    max_gpu: int | None = None
    max_vram_gb: int | None = None


@router.post("/upgrade")
def upgrade(req: UpgradeRequest, db: DbSession, background_tasks: BackgroundTasks) -> dict:
    """승인된 (RAG 합성 포함) 데이터셋으로 continual fine-tuning 잡 제출 — 모델 업그레이드(F10).
    §7.5 튜닝 시작 500건 게이트·F9 리소스 세부설정 동일 적용, 결과는 기존 리더보드(F1)에
    나란히 등재되어 업그레이드 전/후 비교가 가능하다."""
    from app.services.trainer import admit_or_queue

    try:
        job = create_job(db, req.model_id, req.dataset_version, triggered_by="rag_upgrade",
                         max_gpu=req.max_gpu, max_vram_gb=req.max_vram_gb,
                         continual_from_job_id=req.continual_from_job_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    background_tasks.add_task(admit_or_queue, job.job_id)
    return {"job_id": job.job_id, "status": job.status, "record_count": job.record_count,
            "continual_from_job_id": job.continual_from_job_id, "training": "background_started"}
