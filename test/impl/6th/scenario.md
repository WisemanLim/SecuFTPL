# impl/6th 시험 시나리오 — E3: 튜닝 잡·평가 러너·리더보드

| # | 케이스 | 방법 | 기대 |
|---|---|---|---|
| 1 | set_f1 경계 | `test_set_f1_exact_and_empty` | 완전일치=1, 빈=빈=1, 오탐만=0 |
| 2 | 평가 지표 계산 | `test_evaluate_predictions_metrics` | json_valid/severity/attack_f1/exact (tools 스크립트 동작 동일) |
| 3 | 잡 전제조건 | `test_job_requires_model_and_approved_records` | 미등록 모델·미승인 데이터 → 422 |
| 4 | 잡 생명주기+플랜 | `test_job_lifecycle_and_plan` | queued→succeeded, QLoRA 플랜(nf4·r16·4bit), 재완료 409 |
| 5 | 평가→리더보드 | `test_evaluate_endpoint_and_leaderboard_ranking` | attack_f1 내림차순, baseline 표시 |
