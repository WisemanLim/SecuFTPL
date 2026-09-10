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


def decontaminate(candidates: list[dict], eval_records: list[dict], k: int = 13) -> dict:
    """13-gram 디컨탬 (PRD F18, Survey §2.2 — DataTrove 방식 준용).
    후보 레코드가 평가셋과 k-gram(토큰) 하나라도 공유하면 오염으로 표시 — train/test 누수·벤치 오염 방지."""
    eval_shingles: set[str] = set()
    for r in eval_records:
        eval_shingles |= shingles(record_text(r), k)
    contaminated = []
    for r in candidates:
        overlap = shingles(record_text(r), k) & eval_shingles
        if overlap:
            contaminated.append({
                "record_id": (r.get("metadata") or {}).get("record_id"),
                "matched_ngram_sample": min(overlap)[:200],
            })
    return {"k": k, "candidates": len(candidates), "eval_records": len(eval_records),
            "contaminated_count": len(contaminated), "contaminated": contaminated}


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
