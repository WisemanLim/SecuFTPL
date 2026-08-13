# impl/32nd 시험 결과 — F12 평가지표 가이드·추천

- 일시: 2026-08-13
- 판정: **PASS**

| # | 케이스 | 결과 |
|---|---|---|
| 1 | alert_triage 추천 세트 | PASS |
| 2 | 미상 task_type → 기본 폴백 | PASS |
| 3 | case_count 5/50/500 신뢰도 안내 | PASS(3건) |
| 4 | 지표 6종 가이드 문구 존재 | PASS |
| 5 | `GET /eval-guide`(기본) | PASS |
| 6 | `GET /eval-guide?task_type=vuln_triage&case_count=10` | PASS |
| 전체 | `uv run pytest -q` | PASS — 121 passed |
| 린트 | `uv run ruff check .` | PASS |

## 생성/수정 파일

- `app/services/eval_guide.py`(신규) — task_type별 추천 지표·가이드 문구·표본 신뢰도 안내
- `app/api/tuning.py` — `GET /eval-guide` 엔드포인트
- `test/test_eval_guide.py`(신규 6건)

## 잔여

- 없음(F12 범위 완료). PRD F9~F12 전 항목 구현 완료(impl/29th~32nd) — §8 Epic E9~E11 완료로 갱신 필요
