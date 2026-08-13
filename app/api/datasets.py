"""secuftpl — 데이터셋 API (PRD E1: 검증·포맷 변환)."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.formats import EXPORTERS, IMPORTERS, convert
from app.services.gate import validate_records

router = APIRouter(prefix="/api/v1/datasets", tags=["datasets"])


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
