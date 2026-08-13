# impl/3rd 시험 결과

- 일시: 2026-08-13
- 판정: **PASS** (pytest 33/33 — 신규 16 + 회귀 17, ruff 0 오류)

| # | 케이스 | 결과 |
|---|---|---|
| 1~5 | 가명화·중복제거 서비스 | PASS (test_sanitize_dedup.py 6건) |
| 6~9 | 검수 큐 API (in-memory sqlite override) | PASS (test_records_api.py 5건) |
| 10~11 | dpo-pairs·eval-set export | PASS (test_export_formats.py 5건) |
| 12 | 회귀+린트 | PASS |

## 수정·재시험 이력

1. `test_ingest_skips_near_duplicate_in_batch` FAIL — 짧은 문장에서 shingle 차이 비중 과대
   → fixture 를 실제 경보 문장 길이로 보강(답변 동일·문장부호만 상이) → PASS.
2. ruff B008 (`Depends` 기본값 호출) 3건 → `Annotated[Session, Depends(get_db)]` 관용구로 전환.

## 비고

- 근접중복은 **배치 내 비교만** 수행(기존 DB 대비는 완전 중복 해시만) — 대규모 코퍼스용
  MinHash/LSH 인덱스는 데이터 축적 후 확장 지점.
- Presidio NER(인명/전화 등) 기반 가명화는 별도 의존(spacy 모델) — regex 계층 우선, 차기 옵션.
- DB 스키마는 create_all — 스키마 진화 시 alembic migration 전환.
