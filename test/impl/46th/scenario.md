# impl/46th — E14 안전·선호 데이터 (F17) (PRD v0.4, 2026-09-10)

Survey §3 P0+P1 반영(고도화 v0.4, 사용자 범위 승인). PRD 먼저 갱신 후 구현.

## 범위

- jailbreak importer(prompt → safety_refusal 주석대기, T3_untrusted)
- KTO export(만족도 up/likert≥4=true, down/≤2=false, 중립·무평가 제외) — convert·dataset export 포맷 등록

## 시험

test/test_safety_kto.py 3건 + 전체 회귀 `uv run pytest` + `ruff check` + frontend(tsc·Vitest)
