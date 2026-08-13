"""secuftpl — 중복·근접중복 제거 (PRD §7.3 게이트 ⑥).

- 완전 중복: 정규화 텍스트 sha256 (DB content_hash 대조 — train/test 누수 방지)
- 근접 중복: 토큰 3-shingle Jaccard 유사도 (배치 내 비교, 기본 임계 0.9)
"""
import hashlib
import re

_WS_RE = re.compile(r"\s+")


def normalize(text: str) -> str:
    return _WS_RE.sub(" ", text.strip().lower())


def record_text(record: dict) -> str:
    return "\n".join(m["content"] for m in record["messages"])


def content_hash(record: dict) -> str:
    return hashlib.sha256(normalize(record_text(record)).encode()).hexdigest()


def shingles(text: str, k: int = 3) -> set[str]:
    tokens = normalize(text).split()
    if len(tokens) < k:
        return {" ".join(tokens)} if tokens else set()
    return {" ".join(tokens[i : i + k]) for i in range(len(tokens) - k + 1)}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    union = len(a | b)
    return len(a & b) / union if union else 0.0


def find_near_duplicates(records: list[dict], threshold: float = 0.9) -> list[tuple[int, int, float]]:
    """배치 내 근접중복 쌍 (i, j, 유사도). i < j, 유사도 ≥ threshold."""
    shingle_sets = [shingles(record_text(r)) for r in records]
    pairs = []
    for i in range(len(records)):
        for j in range(i + 1, len(records)):
            sim = jaccard(shingle_sets[i], shingle_sets[j])
            if sim >= threshold:
                pairs.append((i, j, round(sim, 4)))
    return pairs
