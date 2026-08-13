"""secuftpl — 모델 레지스트리 API (PRD F2, E2)."""
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.models.registry import ModelRow
from app.services.hf_registry import (
    build_manifest,
    download_plan,
    register_discovered,
    seed_catalog,
)

router = APIRouter(prefix="/api/v1/models", tags=["models"])
DbSession = Annotated[Session, Depends(get_db)]


class SeedRequest(BaseModel):
    profile: str = Field(pattern="^(pilot|core|all)$")


class PinRequest(BaseModel):
    revision: str = Field(min_length=7)  # HF 커밋 해시 (short 이상)


class ScanRequest(BaseModel):
    discovered: list[dict] = Field(min_length=1)
    criteria: list[str] | None = None  # 미지정 시 HF_SIMILARITY_CRITERIA


def _row(db: Session, model_id: str) -> ModelRow:
    row = db.scalar(select(ModelRow).where(ModelRow.model_id == model_id))
    if not row:
        raise HTTPException(status_code=404, detail=f"model not registered: {model_id}")
    return row


@router.post("/seed")
def seed(req: SeedRequest, db: DbSession) -> dict:
    return seed_catalog(db, req.profile)


@router.get("")
def list_models(db: DbSession, status: str | None = None, tier: str | None = None) -> dict:
    q = select(ModelRow).order_by(ModelRow.model_id)
    if status:
        q = q.where(ModelRow.status == status)
    if tier:
        q = q.where(ModelRow.tier == tier)
    rows = db.scalars(q).all()
    return {"count": len(rows), "models": [
        {"model_id": r.model_id, "tier": r.tier, "role": r.role, "family": r.family,
         "param_size_b": r.param_size_b, "status": r.status, "revision": r.revision,
         "source": r.source, "matched_to": r.matched_to} for r in rows
    ]}


@router.get("/{model_id:path}/detail")
def model_detail(model_id: str, db: DbSession) -> dict:
    """모델 상세 — 메타·상태·다운로드 플랜(hf CLI 명령)·스냅샷 매니페스트(다운로드 완료 시)."""
    import json

    from app.services.hf_registry import download_plan
    from app.services.model_download import MODEL_ROOT

    row = _row(db, model_id)
    manifest = None
    snap = MODEL_ROOT / model_id.replace("/", "__") / "snapshot_manifest.json"
    if snap.is_file():
        manifest = json.loads(snap.read_text(encoding="utf-8"))
    return {
        "model_id": row.model_id, "tier": row.tier, "role": row.role, "family": row.family,
        "param_size_b": row.param_size_b, "license": row.license, "status": row.status,
        "revision": row.revision, "source": row.source, "matched_to": row.matched_to,
        "notes": row.notes, "download_plan": download_plan(row),
        "snapshot_manifest": manifest,
        "usable_for_training": row.status in ("downloaded", "pinned"),
    }


@router.get("/manifest")
def manifest(db: DbSession) -> dict:
    return build_manifest(db)


@router.post("/events/scan")
def events_scan(req: ScanRequest, db: DbSession) -> dict:
    """신규 모델 이벤트 스캔 결과 주입 (ops 스케줄러가 HF_POLLING_CRON 주기로 호출)."""
    criteria = req.criteria or [c.strip() for c in settings.hf_similarity_criteria.split(",") if c.strip()]
    return register_discovered(db, req.discovered, criteria)


@router.post("/{model_id:path}/download")
def download(model_id: str, db: DbSession, background_tasks: BackgroundTasks) -> dict:
    """모델 로컬 반입 — registered/candidate → downloading(백그라운드) → downloaded.
    실 다운로드는 worker(hf CLI); 코어는 상태 전환 + 스냅샷 매니페스트(시뮬)."""
    from app.services.model_download import run_download

    row = _row(db, model_id)
    if row.status in ("downloading", "downloaded", "pinned"):
        raise HTTPException(status_code=409, detail=f"already {row.status}")
    row.status = "downloading"
    db.commit()
    background_tasks.add_task(run_download, model_id)
    return {"model_id": model_id, "status": "downloading"}


@router.post("/{model_id:path}/pin")
def pin(model_id: str, req: PinRequest, db: DbSession) -> dict:
    row = _row(db, model_id)
    row.revision = req.revision
    row.status = "pinned"
    db.commit()
    return {"model_id": model_id, "status": "pinned", "revision": req.revision}


@router.get("/{model_id:path}/download-plan")
def get_download_plan(model_id: str, db: DbSession) -> dict:
    row = _row(db, model_id)
    return {"model_id": model_id, "revision": row.revision, "command": download_plan(row)}
