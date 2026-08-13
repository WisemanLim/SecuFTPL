"""secuftpl — 레코드 수집·검수 큐 API (PRD §7.3 ⑤⑥⑨, E1).

수집(ingest) 흐름: 게이트 검증(스키마) → 가명화(안정 토큰, DB 매핑) → 완전 중복 차단(content_hash)
→ 배치 내 근접중복 스킵 → pending 적재. 승인(approve)만 데이터셋 편입, 반려(reject)는 증강본
연쇄 폐기(lineage_of, PRD §7.4).
"""
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db

DbSession = Annotated[Session, Depends(get_db)]


def iso_utc(dt: datetime | None) -> str | None:
    """DB naive 타임스탬프(UTC 저장) → ISO8601 +00:00 — 화면은 locale 변환(PRD 시간 표기 원칙)."""
    if dt is None:
        return None
    return (dt if dt.tzinfo else dt.replace(tzinfo=UTC)).isoformat()
from app.models.records import DatasetRecordRow, PseudonymRow
from app.services.dedup import content_hash, find_near_duplicates
from app.services.gate import validate_record
from app.services.sanitize import sanitize_record

router = APIRouter(prefix="/api/v1/records", tags=["records"])


class IngestRequest(BaseModel):
    records: list[dict] = Field(min_length=1)
    near_dup_threshold: float = Field(default=0.9, ge=0.5, le=1.0)


class ReviewRequest(BaseModel):
    action: str = Field(pattern="^(approve|reject)$")
    reviewer: str = Field(min_length=1)


class AugmentRequest(BaseModel):
    method: str = Field(default="keyword", pattern="^(keyword|backtranslate)$")
    substitutions: dict[str, str] | None = None  # keyword 모드 필수 — 전문가 승인 사전 (PRD §7.4)
    record_ids: list[str] | None = None  # 미지정 시 approved 원본 전체
    near_dup_threshold: float = Field(default=1.0, ge=0.5, le=1.0)  # 증강본은 원본과 유사한 게 정상 — 기본 완전중복만 차단


def _load_mapping(db: Session) -> dict[str, str]:
    return {row.key: row.token for row in db.scalars(select(PseudonymRow))}


def _persist_mapping(db: Session, before: set[str], mapping: dict[str, str]) -> None:
    for key in mapping.keys() - before:
        kind = key.split(":", 1)[0]
        db.add(PseudonymRow(key=key, kind=kind, token=mapping[key]))


@router.post("/ingest")
def ingest(req: IngestRequest, db: DbSession) -> dict:
    mapping = _load_mapping(db)
    known_keys = set(mapping)
    near_dup_idx = {j for _, j, _ in find_near_duplicates(req.records, req.near_dup_threshold)}
    results = []
    for idx, raw in enumerate(req.records):
        errors = validate_record(raw)
        # 가명화 전 원문 기준 게이트: 스키마 오류만 차단, 비밀값/자산 탐지는 가명화로 해소
        schema_errors = [e for e in errors if "detected" not in e]
        if schema_errors:
            results.append({"index": idx, "status": "rejected_gate", "errors": schema_errors})
            continue
        if idx in near_dup_idx:
            results.append({"index": idx, "status": "skipped_near_duplicate"})
            continue
        clean = sanitize_record(raw, mapping)
        chash = content_hash(clean)
        rid = clean["metadata"]["record_id"]
        dup = db.scalar(select(DatasetRecordRow).where(
            (DatasetRecordRow.content_hash == chash) | (DatasetRecordRow.record_id == rid)
        ))
        if dup:
            results.append({"index": idx, "status": "skipped_exact_duplicate", "existing": dup.record_id})
            continue
        db.add(DatasetRecordRow(
            record_id=rid,
            payload=clean,
            content_hash=chash,
            quality_grade=clean["metadata"].get("quality_grade", "silver"),
            lineage_of=clean["metadata"].get("lineage_of"),
        ))
        results.append({"index": idx, "status": "queued", "record_id": rid, "content_hash": chash})
    _persist_mapping(db, known_keys, mapping)
    db.commit()
    queued = sum(1 for r in results if r["status"] == "queued")
    return {"total": len(req.records), "queued": queued, "results": results,
            "pseudonyms_added": len(mapping) - len(known_keys)}


class CollectDirRequest(BaseModel):
    path: str
    pattern: str = "*.jsonl"
    source_format: str = "canonical"
    task_type: str = "alert_triage"
    dataset_version: str = "v0.1.0"


class CollectUrlRequest(BaseModel):
    url: str
    source_format: str = "canonical"
    task_type: str = "alert_triage"
    dataset_version: str = "v0.1.0"


def _collect_defaults(task_type: str, dataset_version: str, source_type: str) -> dict:
    return {"task_type": task_type, "dataset_version": dataset_version,
            "source_type": source_type, "trust_tier": "T2_internal"}


@router.post("/upload")
async def upload(
    db: DbSession,
    files: Annotated[list[UploadFile], File(description="JSONL/JSON 파일 (복수)")],
    source_format: Annotated[str, Form()] = "canonical",
    task_type: Annotated[str, Form()] = "alert_triage",
    dataset_version: Annotated[str, Form()] = "v0.1.0",
) -> dict:
    """파일(멀티) 업로드 수집 — wise-FP 모드 A. 정형(JSONL/JSON) + 문서(PDF/DOCX/TXT/MD/HTML).
    문서는 텍스트 추출 → 주석 대기(needs_annotation) 레코드. 게이트 동일 통과."""
    from app.services.collect import collect_file

    records: list[dict] = []
    reports = []
    for f in files:
        try:
            recs = collect_file(await f.read(), f.filename or "upload.jsonl", source_format,
                                _collect_defaults(task_type, dataset_version, "file_upload"))
            records.extend(recs)
            reports.append({"file": f.filename, "records": len(recs), "status": "ok"})
        except ValueError as exc:  # JSONDecodeError·UnicodeDecodeError 포함
            reports.append({"file": f.filename, "records": 0, "status": f"error: {exc}"})
    if not records:
        raise HTTPException(status_code=422, detail={"message": "no parsable records", "files": reports})
    result = ingest(IngestRequest(records=records), db)
    return {"files": reports, "ingest": result}


@router.post("/collect/dir")
def collect_dir_endpoint(req: CollectDirRequest, db: DbSession) -> dict:
    """디렉토리 일괄 수집 — wise-FP 모드 B (서버 로컬 경로)."""
    from app.services.collect import collect_dir

    try:
        records, reports = collect_dir(
            req.path, req.pattern, req.source_format,
            _collect_defaults(req.task_type, req.dataset_version, "dir_collect"))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if not records:
        raise HTTPException(status_code=422, detail={"message": "no parsable records", "files": reports})
    return {"files": reports, "ingest": ingest(IngestRequest(records=records), db)}


@router.post("/collect/url")
def collect_url_endpoint(req: CollectUrlRequest, db: DbSession) -> dict:
    """인터넷 수집 — wise-FP 모드 C. 화이트리스트+사설 IP 차단, T3_untrusted 태깅."""
    from app.services.collect import collect_url

    try:
        records = collect_url(req.url, req.source_format, {
            "task_type": req.task_type, "dataset_version": req.dataset_version})
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except OSError as exc:
        raise HTTPException(status_code=502, detail=f"fetch failed: {exc}") from exc
    if not records:
        raise HTTPException(status_code=422, detail="no parsable records")
    return {"url": req.url, "ingest": ingest(IngestRequest(records=records), db)}


def _augment_originals(db: Session, record_ids: list[str] | None) -> list[dict]:
    q = select(DatasetRecordRow).where(
        DatasetRecordRow.review_state == "approved",
        DatasetRecordRow.lineage_of.is_(None),  # 증강본의 재증강 금지
    )
    if record_ids:
        q = q.where(DatasetRecordRow.record_id.in_(record_ids))
    return [r.payload for r in db.scalars(q)]


@router.get("/augment/suggestions")
def augment_suggestions(db: DbSession, top_n: int = 10) -> dict:
    """치환 후보 자동 추천 — 승인 레코드 빈도 키워드 × 보안 동의어 사전 (확정은 전문가)."""
    from app.services.augment import suggest_substitutions

    originals = _augment_originals(db, None)
    return {"records_scanned": len(originals),
            "suggestions": suggest_substitutions(originals, top_n)}


@router.post("/augment")
def augment(req: AugmentRequest, db: DbSession) -> dict:
    """승인(approved)된 원본만 증강 → 검수 큐 재편입 (PRD §7.4: 증강본도 게이트·검수 통과 필수).
    method=keyword(치환 사전) | backtranslate(ko→en→ko, Ollama 백엔드)."""
    from app.services.augment import (
        augment_records,
        back_translate_records,
        ollama_translator,
    )

    originals = _augment_originals(db, req.record_ids)
    if not originals:
        raise HTTPException(status_code=422, detail="no approved original records to augment")
    try:
        if req.method == "backtranslate":
            import os

            base = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
            try:
                augmented = back_translate_records(originals, ollama_translator(base))
            except OSError as exc:
                raise HTTPException(
                    status_code=503,
                    detail=f"번역 백엔드(Ollama) 미가용: {exc} — OLLAMA_BASE_URL 확인/기동 필요") from exc
        else:
            if not req.substitutions:
                raise HTTPException(status_code=422, detail="keyword 모드는 substitutions 필수")
            augmented = augment_records(originals, req.substitutions)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if not augmented:
        return {"method": req.method, "originals": len(originals), "augmented": 0, "ingest": None}
    ingest_result = ingest(IngestRequest(records=augmented,
                                         near_dup_threshold=req.near_dup_threshold), db)
    return {"method": req.method, "originals": len(originals),
            "augmented": len(augmented), "ingest": ingest_result}


@router.get("/queue")
def queue(db: DbSession, state: str = "pending") -> dict:
    rows = db.scalars(
        select(DatasetRecordRow).where(DatasetRecordRow.review_state == state)
        .order_by(DatasetRecordRow.id)
    ).all()
    return {"state": state, "count": len(rows), "items": [
        {"record_id": r.record_id, "task_type": r.payload["metadata"].get("task_type"),
         "quality_grade": r.quality_grade, "lineage_of": r.lineage_of,
         "created_at": iso_utc(r.created_at)} for r in rows
    ]}


@router.delete("/{record_id}")
def delete_record(record_id: str, db: DbSession) -> dict:
    """레코드 삭제 — 증강본(lineage)도 연쇄 삭제. UI 는 사용자 확인 팝업 후 호출."""
    row = db.scalar(select(DatasetRecordRow).where(DatasetRecordRow.record_id == record_id))
    if not row:
        raise HTTPException(status_code=404, detail=f"record not found: {record_id}")
    cascaded = [c.record_id for c in db.scalars(select(DatasetRecordRow).where(
        DatasetRecordRow.lineage_of == record_id))]
    for rid in [record_id, *cascaded]:
        target = db.scalar(select(DatasetRecordRow).where(DatasetRecordRow.record_id == rid))
        if target:
            db.delete(target)
    db.commit()
    return {"deleted": record_id, "cascaded_deletes": cascaded}


@router.get("/{record_id}")
def get_record(record_id: str, db: DbSession) -> dict:
    """레코드 상세 — 검수 시 내용(payload) 확인용."""
    row = db.scalar(select(DatasetRecordRow).where(DatasetRecordRow.record_id == record_id))
    if not row:
        raise HTTPException(status_code=404, detail=f"record not found: {record_id}")
    return {
        "record_id": row.record_id, "review_state": row.review_state,
        "quality_grade": row.quality_grade, "lineage_of": row.lineage_of,
        "reviewer": row.reviewer, "content_hash": row.content_hash,
        "created_at": iso_utc(row.created_at), "payload": row.payload,
    }


@router.post("/{record_id}/review")
def review(record_id: str, req: ReviewRequest, db: DbSession) -> dict:
    row = db.scalar(select(DatasetRecordRow).where(DatasetRecordRow.record_id == record_id))
    if not row:
        raise HTTPException(status_code=404, detail=f"record not found: {record_id}")
    if row.review_state != "pending":
        raise HTTPException(status_code=409, detail=f"already {row.review_state}")
    new_state = "approved" if req.action == "approve" else "rejected"
    row.review_state = new_state
    row.reviewer = req.reviewer
    cascaded = []
    if new_state == "rejected":
        # PRD §7.4: 원본 반려 시 증강본 연쇄 폐기
        for child in db.scalars(select(DatasetRecordRow).where(
            DatasetRecordRow.lineage_of == record_id,
            DatasetRecordRow.review_state != "rejected",
        )):
            child.review_state = "rejected"
            child.reviewer = req.reviewer
            cascaded.append(child.record_id)
    db.commit()
    return {"record_id": record_id, "review_state": new_state,
            "reviewer": req.reviewer, "cascaded_rejects": cascaded}
