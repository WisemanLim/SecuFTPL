# impl/8th 시험 시나리오 — E5: Agent 피드백 환류

| # | 케이스 | 방법 | 기대 |
|---|---|---|---|
| 1 | 환류 수집 | `test_feedback_ingests_to_review_queue` | 질의/답변+만족도 → canonical(fb-해시) → pending 큐, 중복 차단 |
| 2 | 스키마 검증 | `test_feedback_scale_validation_and_likert` | binary 에 3점 → 422, likert5 4점 OK (§7.9) |
| 3 | 만족도 집계 | `test_feedback_down_and_stats` | up/down/up_ratio/by_state (§5 만족도 지표) |
| 4 | 게이트 동일 적용 | `test_feedback_sanitized` | 질의 내 내부IP·호스트 가명화 (환류에도 §7.3 ⑤) |
