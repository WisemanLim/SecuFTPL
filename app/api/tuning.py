"""secuftpl — 튜닝·평가·리더보드 API (PRD E3)."""
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.records import iso_utc
from app.core.db import get_db
from app.models.tuning import TuningJobRow
from app.services.evaluate import evaluate_predictions
from app.services.tuning import (
    complete_job,
    create_job,
    leaderboard,
    record_eval,
    train_plan,
)

router = APIRouter(prefix="/api/v1/tuning", tags=["tuning"])
DbSession = Annotated[Session, Depends(get_db)]


class JobCreate(BaseModel):
    model_id: str
    dataset_version: str


class JobComplete(BaseModel):
    status: str = Field(pattern="^(succeeded|failed)$")
    adapter_uri: str | None = None
    metrics: dict | None = None
    error: str | None = None


class EvaluateRequest(BaseModel):
    model_id: str
    dataset_version: str
    rows: list[dict] = Field(min_length=1)  # [{"expected": {...}, "prediction": ...}]
    job_id: str | None = None  # None = 무튜닝 베이스라인


def _job(db: Session, job_id: str) -> TuningJobRow:
    job = db.scalar(select(TuningJobRow).where(TuningJobRow.job_id == job_id))
    if not job:
        raise HTTPException(status_code=404, detail=f"job not found: {job_id}")
    return job


@router.post("/jobs")
def post_job(req: JobCreate, db: DbSession, background_tasks: BackgroundTasks) -> dict:
    try:
        job = create_job(db, req.model_id, req.dataset_version)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    # 학습 워커 백그라운드 실행 (PRD §7.5 — real/simulate 자동 선택)
    from app.services.trainer import run_training_job

    background_tasks.add_task(run_training_job, job.job_id)
    return {"job_id": job.job_id, "status": job.status, "record_count": job.record_count,
            "training": "background_started"}


@router.get("/jobs/{job_id}/events")
def job_events(job_id: str, db: DbSession) -> dict:
    """잡 진행 이벤트 폴링 (손실 곡선·단계 로그)."""
    from app.api.records import iso_utc
    from app.services.trainer import JobEventRow

    _job(db, job_id)  # 404 검증
    rows = db.scalars(select(JobEventRow).where(JobEventRow.job_id == job_id)
                      .order_by(JobEventRow.id)).all()
    return {"job_id": job_id, "count": len(rows), "events": [
        {"message": r.message, "at": iso_utc(r.created_at)} for r in rows]}


@router.get("/leaderboard/detail/{model_id:path}")
def leaderboard_detail(model_id: str, db: DbSession) -> dict:
    """리더보드 모델 상세 — 평가 이력 전체 + 관련 튜닝 잡."""
    from app.api.records import iso_utc
    from app.models.tuning import EvalResultRow

    evals = db.scalars(select(EvalResultRow).where(EvalResultRow.model_id == model_id)
                       .order_by(EvalResultRow.id.desc())).all()
    if not evals:
        raise HTTPException(status_code=404, detail=f"no evaluation results: {model_id}")
    jobs = db.scalars(select(TuningJobRow).where(TuningJobRow.model_id == model_id)
                      .order_by(TuningJobRow.id.desc())).all()
    return {
        "model_id": model_id,
        "evaluations": [{
            "eval_id": e.id, "dataset_version": e.dataset_version, "job_id": e.job_id,
            "baseline": e.job_id is None, "cases": e.cases,
            "json_valid_rate": e.json_valid_rate, "severity_accuracy": e.severity_accuracy,
            "exact_match_rate": e.exact_match_rate, "attack_f1": e.attack_f1,
            "attack_precision": e.attack_precision, "attack_recall": e.attack_recall,
            "at": iso_utc(e.created_at)} for e in evals],
        "jobs": [{
            "job_id": j.job_id, "dataset_version": j.dataset_version, "status": j.status,
            "record_count": j.record_count, "adapter_uri": j.adapter_uri,
            "triggered_by": j.triggered_by, "at": iso_utc(j.created_at)} for j in jobs],
    }


@router.get("/jobs")
def list_jobs(db: DbSession, status: str | None = None) -> dict:
    q = select(TuningJobRow).order_by(TuningJobRow.id.desc())
    if status:
        q = q.where(TuningJobRow.status == status)
    rows = db.scalars(q).all()
    return {"count": len(rows), "jobs": [
        {"job_id": j.job_id, "model_id": j.model_id, "dataset_version": j.dataset_version,
         "record_count": j.record_count, "status": j.status, "adapter_uri": j.adapter_uri,
         "progress_pct": j.progress_pct, "current_step": j.current_step,
         "total_steps": j.total_steps, "error": j.error,
         "triggered_by": j.triggered_by, "created_at": iso_utc(j.created_at)} for j in rows
    ]}


@router.get("/jobs/{job_id}/export")
def export_model(job_id: str, db: DbSession):
    """succeeded 잡 결과물(어댑터) tar.gz 스트리밍 다운로드 (wise-FP Stage9 package 상당)."""
    import io
    import tarfile
    from pathlib import Path

    from fastapi.responses import StreamingResponse

    job = _job(db, job_id)
    if job.status != "succeeded" or not job.adapter_uri:
        raise HTTPException(status_code=409, detail="succeeded 잡만 export 가능")
    adapter_dir = Path(job.adapter_uri)
    if not adapter_dir.is_dir():
        raise HTTPException(status_code=404, detail=f"adapter not found: {adapter_dir}")
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        tar.add(adapter_dir, arcname=job_id)
    buf.seek(0)
    return StreamingResponse(
        buf, media_type="application/gzip",
        headers={"Content-Disposition": f'attachment; filename="{job_id}.tar.gz"'})


@router.post("/jobs/{job_id}/retry")
def retry_job(job_id: str, db: DbSession, background_tasks: BackgroundTasks) -> dict:
    """queued/failed 잡 재실행 — 백그라운드 워커에 재투입 (running/succeeded 는 차단)."""
    from app.services.trainer import run_training_job

    job = _job(db, job_id)
    if job.status not in ("queued", "failed"):
        raise HTTPException(status_code=409,
                            detail=f"cannot retry job in status '{job.status}' (queued/failed 만 가능)")
    job.status = "queued"
    job.error = None
    db.commit()
    background_tasks.add_task(run_training_job, job_id)
    return {"job_id": job_id, "status": "queued", "retry": "background_started"}


@router.delete("/jobs/{job_id}")
def delete_job(job_id: str, db: DbSession) -> dict:
    """잡 삭제 — 이벤트 로그 연쇄 삭제 (running 은 차단). 평가 결과는 이력으로 유지."""
    from app.services.trainer import JobEventRow

    job = _job(db, job_id)
    if job.status == "running":
        raise HTTPException(status_code=409, detail="running 잡은 삭제할 수 없음 (완료/실패 후 삭제)")
    for ev in db.scalars(select(JobEventRow).where(JobEventRow.job_id == job_id)):
        db.delete(ev)
    db.delete(job)
    db.commit()
    return {"deleted": job_id}


@router.get("/jobs/{job_id}/plan")
def get_plan(job_id: str, db: DbSession) -> dict:
    job = _job(db, job_id)
    return {"job_id": job_id, "plan": train_plan(job)}


@router.post("/jobs/{job_id}/complete")
def post_complete(job_id: str, req: JobComplete, db: DbSession) -> dict:
    try:
        job = complete_job(db, job_id, req.status, req.adapter_uri, req.metrics, req.error)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"job_id": job.job_id, "status": job.status, "adapter_uri": job.adapter_uri}


@router.get("/eval-template")
def eval_template(db: DbSession, dataset_version: str | None = None, limit: int = 20) -> dict:
    """승인 레코드의 정답(assistant JSON)에서 평가 지표 행을 자동 생성 —
    expected 추출 + prediction=expected 출발점(사용자 수정 후 또는 그대로 판정 가능)."""
    import json

    from app.models.records import DatasetRecordRow

    approved = db.scalars(select(DatasetRecordRow).where(
        DatasetRecordRow.review_state == "approved")).all()
    rows = []
    skipped = 0
    for r in approved:
        meta = r.payload.get("metadata", {})
        if dataset_version and meta.get("dataset_version") != dataset_version:
            continue
        try:
            answer = json.loads(r.payload["messages"][-1]["content"])
        except (json.JSONDecodeError, KeyError, IndexError):
            skipped += 1
            continue
        if answer.get("status") == "needs_annotation":  # 문서 수집 미주석 레코드 제외
            skipped += 1
            continue
        attack_ids = answer.get("attack_ids") or [
            m.get("technique_id") for m in answer.get("attack_mapping", []) if m.get("technique_id")]
        expected = {"severity": answer.get("severity"), "attack_ids": attack_ids}
        rows.append({"record_id": r.record_id, "expected": expected, "prediction": dict(expected)})
        if len(rows) >= limit:
            break
    return {"count": len(rows), "skipped_unparsable": skipped, "rows": rows}


@router.post("/evaluate")
def post_evaluate(req: EvaluateRequest, db: DbSession) -> dict:
    """예측 배치 평가 → 지표 계산 → 리더보드 반영."""
    metrics = evaluate_predictions(req.rows)
    record_eval(db, req.model_id, req.dataset_version, metrics, job_id=req.job_id)
    return {"model_id": req.model_id, "dataset_version": req.dataset_version, **metrics}


@router.get("/leaderboard")
def get_leaderboard(db: DbSession, dataset_version: str | None = None,
                    sort_by: str = "attack_f1") -> dict:
    items = leaderboard(db, dataset_version, sort_by)
    return {"count": len(items), "sort_by": sort_by, "items": items}


@router.delete("/leaderboard/{eval_id}")
def delete_eval(eval_id: int, db: DbSession) -> dict:
    """리더보드 평가 결과 1건 삭제 (잡·모델은 유지)."""
    from app.models.tuning import EvalResultRow

    row = db.scalar(select(EvalResultRow).where(EvalResultRow.id == eval_id))
    if not row:
        raise HTTPException(status_code=404, detail=f"eval result not found: {eval_id}")
    db.delete(row)
    db.commit()
    return {"deleted_eval_id": eval_id}
