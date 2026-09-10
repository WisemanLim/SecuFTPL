"""secuftpl — canonical 데이터셋 스키마 (PRD §7.2 sft-messages).

내부 정규 포맷: SFT messages JSONL + metadata. 모든 외부 포맷은 이 모델과
양방향 변환 어댑터(app/services/formats.py)를 거친다.
"""
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

Role = Literal["system", "user", "assistant"]
QualityGrade = Literal["gold", "silver", "augmented"]
ReviewState = Literal["pending", "approved", "rejected"]
SatisfactionScale = Literal["binary", "likert5"]


class Message(BaseModel):
    role: Role
    content: str = Field(min_length=1)


class Satisfaction(BaseModel):
    """만족도 (PRD §7.9 SATISFACTION_SCALE) — binary(up/down)·likert5(1~5) 모두 저장 가능."""

    scale: SatisfactionScale = "binary"
    score: str | int
    reason_tags: list[str] = []
    rated_by: Literal["user", "analyst"] = "user"
    rated_at: str | None = None

    @model_validator(mode="after")
    def check_score_matches_scale(self) -> "Satisfaction":
        if self.scale == "binary" and self.score not in ("up", "down"):
            raise ValueError("binary scale requires score 'up' or 'down'")
        if self.scale == "likert5" and self.score not in (1, 2, 3, 4, 5):
            raise ValueError("likert5 scale requires integer score 1..5")
        return self


class RecordMetadata(BaseModel):
    """데이터 계약 필수 메타데이터 (PRD §7.2 — 출처·계보·승인 없는 데이터 반입 금지)."""

    record_id: str
    source_type: str
    task_type: str
    language: str = "ko"
    quality_grade: QualityGrade = "silver"
    review_state: ReviewState = "pending"
    dataset_version: str
    sensitivity: str = "internal"
    license: str = "internal-restricted"
    source_uri: str | None = None
    source_hash_sha256: str | None = None
    ingested_at: str | None = None
    trust_tier: str | None = None
    reviewer: str | None = None
    lineage_of: str | None = None  # 증강본의 원본 record_id (PRD §7.4 연쇄 폐기용)
    # DPI(Data Provenance Initiative) 정렬 선택 필드 (PRD F18, Survey §2.2)
    creator: str | None = None            # 원 데이터 작성 주체(조직/개인)
    license_url: str | None = None        # 라이선스 원문 URI
    provenance_notes: str | None = None   # 계보·수집 경위 비고
    satisfaction: Satisfaction | None = None


class CanonicalRecord(BaseModel):
    """canonical sft-messages 레코드 한 건."""

    messages: list[Message] = Field(min_length=2)
    metadata: RecordMetadata

    @field_validator("messages")
    @classmethod
    def check_roles(cls, v: list[Message]) -> list[Message]:
        roles = [m.role for m in v]
        if "user" not in roles:
            raise ValueError("at least one user message is required")
        if roles[-1] != "assistant":
            raise ValueError("last message must have assistant role")
        return v
