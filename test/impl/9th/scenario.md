# impl/9th 시험 시나리오 — E6: 야간 배치 자동화 (+E7-lite: Supervisor 확장)

| # | 케이스 | 방법 | 기대 |
|---|---|---|---|
| 1 | schedule 모드 | `test_batch_schedule_mode_creates_jobs_for_pinned` | pinned 모델별 잡 생성(triggered_by=batch), 이력 기록 |
| 2 | record_count 임계 | `test_batch_record_count_threshold_skips` | 500 미달 → skipped, should-run false |
| 3 | pinned 없음 | `test_batch_no_pinned_model_skips` | skipped_no_pinned_model |
| 4 | 평가 게이트 | `test_evaluation_gate_pass_block_regression` | 하한 충족+무회귀=통과, f1 회귀=차단, 결과 없음=차단 |
| 5 | CLI 노출 | `secuftpl tune/batch --help` | create/plan/leaderboard·run/gate/runs |
| 6 | Supervisor 확장 | 수동 — ⑤튜닝 잡 제출·플랜, ⑥리더보드·배치 | 버튼 활성화 (E3 완료로 해제) |
