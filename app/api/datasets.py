"""secuftpl — 데이터셋 API (PRD E1: 검증·포맷 변환 + F13 export·F15 run 추적)."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.records import DatasetRecordRow, PipelineRunRow
from app.services.dataset_export import (
    EXPORT_FORMATS,
    build_manifest,
    build_zip,
    filter_by_version,
    to_jsonl,
)
from app.services.formats import EXPORTERS, IMPORTERS, convert
from app.services.gate import validate_records

router = APIRouter(prefix="/api/v1/datasets", tags=["datasets"])
DbSession = Annotated[Session, Depends(get_db)]


class ValidateRequest(BaseModel):
    records: list[dict] = Field(min_length=1)


class ConvertRequest(BaseModel):
    items: list[dict] = Field(min_length=1)
    source: str
    target: str
    meta_defaults: dict = {}


@router.get("/formats")
def list_formats() -> dict:
    return {
        "canonical": "sft-messages",
        "import": sorted(IMPORTERS),
        "export": sorted(EXPORTERS),
    }


@router.post("/validate")
def validate(req: ValidateRequest) -> dict:
    """canonical 레코드 배치 검증 — 정제 게이트 ④(비밀값/자산)·⑦(스키마) 리포트."""
    return validate_records(req.records)


@router.post("/convert")
def convert_records(req: ConvertRequest) -> dict:
    try:
        items = convert(req.items, req.source, req.target, req.meta_defaults)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except (KeyError, TypeError) as exc:
        raise HTTPException(status_code=422, detail=f"malformed item for format '{req.source}': {exc}") from exc
    return {"count": len(items), "items": items}


@router.get("/export")
def export_dataset(
    db: DbSession,
    format: str = "canonical",
    review_state: str = "approved",
    dataset_version: str | None = None,
    with_manifest: bool = False,
) -> Response:
    """데이터셋 다운로드 (F13 §7.15) — 조건 필터 → F6 변환 → JSONL 스트림.
    with_manifest=true 면 zip(dataset+manifest: 출처 집계·sha256 — 전문가 검증 증빙)."""
    if format not in EXPORT_FORMATS:
        raise HTTPException(status_code=422, detail=f"unsupported format: {format} (지원: {EXPORT_FORMATS})")
    if review_state not in ("approved", "pending", "rejected", "all"):
        raise HTTPException(status_code=422, detail=f"invalid review_state: {review_state}")
    q = select(DatasetRecordRow).order_by(DatasetRecordRow.id)
    if review_state != "all":
        q = q.where(DatasetRecordRow.review_state == review_state)
    payloads = filter_by_version([r.payload for r in db.scalars(q)], dataset_version)
    if not payloads:
        raise HTTPException(status_code=404, detail="no records match the given filters")
    try:
        jsonl = to_jsonl(payloads, format)
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=422, detail=f"convert failed: {exc}") from exc
    stem = f"secuftpl-dataset-{dataset_version or 'all'}-{review_state}-{format}"
    if with_manifest:
        manifest = build_manifest(payloads, format, dataset_version, review_state, jsonl)
        return Response(build_zip(jsonl, manifest, format), media_type="application/zip",
                        headers={"Content-Disposition": f'attachment; filename="{stem}.zip"'})
    return Response(jsonl, media_type="application/x-ndjson",
                    headers={"Content-Disposition": f'attachment; filename="{stem}.jsonl"'})


@router.get("/export/manifest")
def export_manifest(
    db: DbSession,
    format: str = "canonical",
    review_state: str = "approved",
    dataset_version: str | None = None,
) -> dict:
    """manifest 만 JSON 으로 조회 (다운로드 전 미리보기·출처 검증용, F13·F14)."""
    if format not in EXPORT_FORMATS:
        raise HTTPException(status_code=422, detail=f"unsupported format: {format} (지원: {EXPORT_FORMATS})")
    q = select(DatasetRecordRow).order_by(DatasetRecordRow.id)
    if review_state != "all":
        q = q.where(DatasetRecordRow.review_state == review_state)
    payloads = filter_by_version([r.payload for r in db.scalars(q)], dataset_version)
    if not payloads:
        raise HTTPException(status_code=404, detail="no records match the given filters")
    try:
        jsonl = to_jsonl(payloads, format)
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=422, detail=f"convert failed: {exc}") from exc
    return build_manifest(payloads, format, dataset_version, review_state, jsonl)


@router.get("/decontam")
def decontam(db: DbSession, train_version: str, eval_version: str, k: int = 13,
             review_state: str = "approved") -> dict:
    """13-gram 디컨탬 리포트 (F18) — train 후보 vs 평가셋 k-gram 오염 검사 (검사만, 삭제 없음)."""
    if not 3 <= k <= 50:
        raise HTTPException(status_code=422, detail="k must be within 3..50")
    q = select(DatasetRecordRow).order_by(DatasetRecordRow.id)
    if review_state != "all":
        q = q.where(DatasetRecordRow.review_state == review_state)
    payloads = [r.payload for r in db.scalars(q)]
    train = filter_by_version(payloads, train_version)
    evals = filter_by_version(payloads, eval_version)
    if not train or not evals:
        raise HTTPException(status_code=404,
                            detail=f"records not found (train={len(train)}, eval={len(evals)})")
    from app.services.dedup import decontaminate

    return {"train_version": train_version, "eval_version": eval_version,
            **decontaminate(train, evals, k)}


@router.get("/export/lmeval-task")
def export_lmeval_task(db: DbSession, dataset_version: str | None = None,
                       review_state: str = "approved") -> Response:
    """lm-evaluation-harness 태스크 YAML (F16) — eval-set JSONL export 와 짝으로 사용."""
    q = select(DatasetRecordRow).order_by(DatasetRecordRow.id)
    if review_state != "all":
        q = q.where(DatasetRecordRow.review_state == review_state)
    payloads = filter_by_version([r.payload for r in db.scalars(q)], dataset_version)
    if not payloads:
        raise HTTPException(status_code=404, detail="no records match the given filters")
    from app.services.dataset_export import lmeval_task_yaml

    stem = f"secuftpl-dataset-{dataset_version or 'all'}-{review_state}-eval-set"
    yaml_text = lmeval_task_yaml(dataset_version, f"{stem}.jsonl")
    return Response(yaml_text, media_type="text/yaml",
                    headers={"Content-Disposition": f'attachment; filename="{stem}.task.yaml"'})


@router.get("/runs")
def list_runs(db: DbSession, channel: str | None = None, limit: int = 50) -> dict:
    """수집·정제 파이프라인 run 이력 (F15 §7.15) — 단계별 통계·출처 집계, append-only."""
    q = select(PipelineRunRow).order_by(PipelineRunRow.id.desc()).limit(max(1, min(limit, 500)))
    if channel:
        q = q.where(PipelineRunRow.channel == channel)
    rows = db.scalars(q).all()
    return {"count": len(rows), "items": [
        {"run_id": r.run_id, "channel": r.channel, "stats": r.stats,
         "created_at": r.created_at.isoformat() if r.created_at else None} for r in rows
    ]}


@router.get("/runs/{run_id}")
def get_run(run_id: str, db: DbSession) -> dict:
    """run 상세 — 차단 사유 샘플 + 출처별 집계 (전문가 검증 근거 자료)."""
    row = db.scalar(select(PipelineRunRow).where(PipelineRunRow.run_id == run_id))
    if not row:
        raise HTTPException(status_code=404, detail=f"run not found: {run_id}")
    return {"run_id": row.run_id, "channel": row.channel, "stats": row.stats,
            "sources": row.sources,
            "created_at": row.created_at.isoformat() if row.created_at else None}
