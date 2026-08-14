"""secuftpl — Agent 피드백 환류 API (PRD F4·§7.3 P0 소스, E5).

AI Assistant 의 질의/답변 + 만족도 → canonical 레코드 조립 → 동일 정제 게이트
(가명화·중복제거) 통과 후 검수 큐 적재. 👎 는 자동 편입 금지 — 검수 큐에서 교정 후
승격하거나 DPO rejected 로 보관(§7.3 환류 규칙). 만족도 스키마: SATISFACTION_SCALE(§7.9).
"""
import hashlib
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.records import IngestRequest, ingest_records
from app.core.config import settings
from app.core.db import get_db
from app.core.schemas import Satisfaction
from app.models.records import DatasetRecordRow

router = APIRouter(prefix="/api/v1/feedback", tags=["feedback"])
DbSession = Annotated[Session, Depends(get_db)]


class FeedbackIn(BaseModel):
    question: str = Field(min_length=1)
    answer: str = Field(min_length=1)
    score: str | int  # binary: up/down · likert5: 1~5
    scale: str | None = None  # 미지정 시 SATISFACTION_SCALE
    reason_tags: list[str] = []
    task_type: str = "alert_triage"
    model_version: str | None = None
    rated_by: str = "user"
    dataset_version: str = "feedback-v0"


@router.post("")
def submit(req: FeedbackIn, db: DbSession) -> dict:
    scale = req.scale or getattr(settings, "satisfaction_scale", "binary")
    try:
        sat = Satisfaction(scale=scale, score=req.score,
                           reason_tags=req.reason_tags, rated_by=req.rated_by)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    rid = "fb-" + hashlib.sha256(f"{req.question}\n{req.answer}".encode()).hexdigest()[:16]
    record = {
        "messages": [
            {"role": "user", "content": req.question},
            {"role": "assistant", "content": req.answer},
        ],
        "metadata": {
            "record_id": rid,
            "source_type": "assistant_feedback",
            "task_type": req.task_type,
            "dataset_version": req.dataset_version,
            # 👍=gold 후보(silver 로 적재, 검수 승인 시 승격 판단) / 👎=silver + 교정 필요
            "quality_grade": "silver",
            "satisfaction": sat.model_dump(),
            # F14 출처 필수: 세션/질의 기반 URI + 원문 hash 스탬핑
            "source_uri": f"assistant://{req.model_version or 'unknown'}/{rid}",
            "source_hash_sha256": hashlib.sha256(f"{req.question}\n{req.answer}".encode()).hexdigest(),
        },
    }
    result = ingest_records(IngestRequest(records=[record]), db, channel="assistant_feedback")
    return {"record_id": rid, "satisfaction": sat.model_dump(), "ingest": result}


@router.get("/stats")
def stats(db: DbSession) -> dict:
    """만족도 집계 (§5 만족도 지표·§7.7 로깅 요구)."""
    rows = db.scalars(select(DatasetRecordRow).where(
        DatasetRecordRow.record_id.like("fb-%"))).all()
    up = down = likert_sum = likert_n = 0
    for r in rows:
        sat = (r.payload.get("metadata") or {}).get("satisfaction") or {}
        score = sat.get("score")
        if score == "up":
            up += 1
        elif score == "down":
            down += 1
        elif isinstance(score, int):
            likert_sum += score
            likert_n += 1
    total = len(rows)
    return {
        "total": total, "up": up, "down": down,
        "up_ratio": up / (up + down) if (up + down) else None,
        "likert_avg": likert_sum / likert_n if likert_n else None,
        "by_state": {
            state: db.scalar(
                select(func.count()).select_from(DatasetRecordRow).where(
                    DatasetRecordRow.record_id.like("fb-%"),
                    DatasetRecordRow.review_state == state,
                )
            )
            for state in ("pending", "approved", "rejected")
        },
    }
