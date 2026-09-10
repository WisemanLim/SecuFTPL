# impl/47th — E15 정제 게이트 고도화 (F18) (PRD v0.4, 2026-09-10)

Survey §3 P0+P1 반영(고도화 v0.4, 사용자 범위 승인). PRD 먼저 갱신 후 구현.

## 범위

- `decontaminate()` 13-gram 디컨탬 + `GET /datasets/decontam?train_version=&eval_version=&k=`
- DPI 선택 필드(creator/license_url/provenance_notes) 스키마 추가 + export manifest 반영

## 시험

test/test_decontam_dpi.py 3건 + 전체 회귀 `uv run pytest` + `ruff check` + frontend(tsc·Vitest)
