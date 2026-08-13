# impl/3rd 시험 시나리오 — E1 잔여 (게이트 ⑤⑥⑨ + F6 export 완성)

범위: 가명화(안정 토큰+DB 매핑), 중복·근접중복 제거, 검수 큐(승인/반려+lineage 연쇄 폐기),
dpo-pairs·eval-set export.

| # | 케이스 | 방법 | 기대 |
|---|---|---|---|
| 1 | 안정 토큰 일관성 | `test_stable_token_consistency` | 동일 원문=동일 토큰, 신규 원문=순번 증가 |
| 2 | 비밀값 토큰 치환 | `test_secret_replaced_with_token` | AWS 키 원문 소거, `<AWS_ACCESS_KEY_0001>` |
| 3 | 원본 불변 가명화 | `test_sanitize_record_immutable` | 새 dict 반환, 원본 유지 |
| 4 | 해시 정규화 | `test_content_hash_normalization` | 공백 차이 무시 동일 해시 |
| 5 | 근접중복 탐지 | `test_find_near_duplicates` | Jaccard 임계 기반 쌍 검출 |
| 6 | ingest 가명화+적재 | `test_ingest_sanitizes_and_queues` | queued=1, 매핑 2건 영속화 |
| 7 | 스키마 차단·완전중복 | `test_ingest_blocks_schema_error_and_exact_dup` | rejected_gate / skipped_exact_duplicate |
| 8 | 배치 근접중복 스킵 | `test_ingest_skips_near_duplicate_in_batch` | 후행 레코드 skipped_near_duplicate |
| 9 | 검수 승인·반려·연쇄 | `test_review_approve_and_reject_cascade` | 원본 reject → 증강본(lineage) 연쇄 폐기, 재검수 409 |
| 10 | eval-set export | `test_eval_set_export` | prompt(정답 제외)+expected |
| 11 | DPO binary/likert5 | `test_dpo_pairs_*` | up/down·4~5/1~2 쌍, 3점 제외, 타 prompt 미결합 |
| 12 | 회귀 + 린트 | 전체 pytest + ruff | 기존 17건 포함 전건 통과 |
