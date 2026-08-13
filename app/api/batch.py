"""secuftpl — 야간 배치 API (PRD F5, E6). ops 스케줄러(FT_TRIGGER_SCHEDULE_CRON)가 호출."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.records import iso_utc
from app.core.db import get_db
from app.services.batch import BatchRunRow, evaluation_gate, run_batch, should_run

router = APIRouter(prefix="/api/v1/batch", tags=["batch"])
DbSession = Annotated[Session, Depends(get_db)]


class BatchRunRequest(BaseModel):
    mode: str | None = None  # 미지정 시 FT_TRIGGER_MODE


class GateRequest(BaseModel):
    model_id: str
    dataset_version: str


@router.get("/should-run")
def get_should_run(db: DbSession, mode: str | None = None) -> dict:
    try:
        ok, detail = should_run(db, mode)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"should_run": ok, "detail": detail}


@router.post("/run")
def post_run(req: BatchRunRequest, db: DbSession) -> dict:
    try:
        return run_batch(db, req.mode)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/gate")
def post_gate(req: GateRequest, db: DbSession) -> dict:
    """배포 게이트 판정 — 통과 시에만 재배포(어댑터 교체), 미통과=차단·이전 버전 유지."""
    return evaluation_gate(db, req.model_id, req.dataset_version)


@router.get("/cron-plan")
def get_cron_plan(base_url: str = "http://127.0.0.1:8000") -> dict:
    """야간 배치·HF polling crontab 라인 생성 — 실행/설치 없음(ops 가 `crontab -e` 로 직접 반영)."""
    from app.services.ops_cron import cron_plan

    return {"base_url": base_url, "command": cron_plan(base_url)}


@router.get("/runs")
def list_runs(db: DbSession) -> dict:
    rows = db.scalars(select(BatchRunRow).order_by(BatchRunRow.id.desc())).all()
    return {"count": len(rows), "runs": [
        {"run_id": r.run_id, "trigger_mode": r.trigger_mode, "status": r.status,
         "dataset_version": r.dataset_version, "jobs": r.jobs,
         "detail": r.trigger_detail, "created_at": iso_utc(r.created_at)} for r in rows
    ]}
