"""secuftpl — 가명화 (PRD §7.3 게이트 ⑤).

삭제 대신 안정 토큰 치환(<INTERNAL_IP_0001>) — 문맥 보존, 동일 원문은 항상 동일 토큰.
mapping 은 별도 보관(DB pseudonym_map, API 계층에서 영속화) — 학습 데이터에 원문 미포함.
비밀값(SECRET_PATTERNS)은 복원 필요가 없으므로 동일 메커니즘으로 <API_KEY_0001> 치환.
"""
import re

from app.services.gate import ASSET_PATTERNS, SECRET_PATTERNS

_ALL_PATTERNS: dict[str, re.Pattern[str]] = {**SECRET_PATTERNS, **ASSET_PATTERNS}


def stable_token(kind: str, value: str, mapping: dict[str, str]) -> str:
    """kind별 순번 안정 토큰. mapping 키 = 'KIND:원문'."""
    key = f"{kind}:{value}"
    if key not in mapping:
        seq = sum(1 for k in mapping if k.startswith(f"{kind}:")) + 1
        mapping[key] = f"<{kind}_{seq:04d}>"
    return mapping[key]


def sanitize_text(text: str, mapping: dict[str, str]) -> str:
    for kind, pattern in _ALL_PATTERNS.items():
        text = pattern.sub(lambda m, k=kind: stable_token(k, m.group(0), mapping), text)
    return text


def sanitize_record(record: dict, mapping: dict[str, str]) -> dict:
    """canonical 레코드의 message content 전체 가명화 (원본 불변, 새 dict 반환)."""
    out = {**record, "messages": [
        {**m, "content": sanitize_text(m["content"], mapping)} for m in record["messages"]
    ]}
    return out
