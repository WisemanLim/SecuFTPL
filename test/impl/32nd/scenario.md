# impl/32nd — F12 평가지표 가이드·추천

근거: PRD `.docs/SecuFTPL-PRD.md` F12(§3).

## 범위

- `GET /api/v1/tuning/eval-guide?task_type=&case_count=` — task_type 별 추천 평가지표 세트
  (§5 지표 재사용, 신규 계산 없음) + 지표 가이드 문구 + 표본 규모 기반 신뢰도 안내.

## 시나리오

| # | 케이스 | 기대 결과 |
|---|---|---|
| 1 | task_type=alert_triage | [severity_accuracy, attack_f1, json_valid_rate] |
| 2 | task_type 미상(unknown_task) | 기본 추천 세트로 폴백 |
| 3 | case_count=5/50/500 | 각각 "30건 미만"/"30~100건"/"100건 이상" 안내 |
| 4 | 지표 6종 전체 가이드 문구 존재 | 모두 non-empty |
| 5 | `GET /eval-guide`(기본값) | task_type=alert_triage, attack_f1 포함 |
| 6 | `GET /eval-guide?task_type=vuln_triage&case_count=10` | 신뢰도 안내에 "30건 미만" 포함 |

## 실행

`uv run pytest -q test/test_eval_guide.py -v` + 전체 회귀 `uv run pytest -q` + `uv run ruff check .`
