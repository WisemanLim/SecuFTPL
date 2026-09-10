# impl/49th — E17 문서 파싱 백엔드 (F20) (PRD v0.4, 2026-09-10)

Survey §3 P0+P1 반영(고도화 v0.4, 사용자 범위 승인). PRD 먼저 갱신 후 구현.

## 범위

- `DOC_PARSER=auto|pypdf|docling` — auto=docling 있으면 사용·없으면 pypdf 폴백, docling 명시+미설치=오류(가짜 성공 없음)

## 시험

test/test_docparser_coverage.py F20 3건 + 전체 회귀 `uv run pytest` + `ruff check` + frontend(tsc·Vitest)
