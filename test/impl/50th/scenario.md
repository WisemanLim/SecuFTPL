# impl/50th — E18 RAG 합성 고도화 (F21) (PRD v0.4, 2026-09-10)

Survey §3 P0+P1 반영(고도화 v0.4, 사용자 범위 승인). PRD 먼저 갱신 후 구현.

## 범위

- `coverage_synthesize()` — 질문 유형 5종 회전 + 청크 키워드 명시 + 커버리지 리포트(covered/uncovered)
- `/rag/synthesize` `diversify=true` 옵션(응답에 coverage 포함)

## 시험

test/test_docparser_coverage.py F21 3건 + 전체 회귀 `uv run pytest` + `ruff check` + frontend(tsc·Vitest)
