# impl/4th 시험 시나리오 — E2 HF 모델 레지스트리 (PRD F2·§7.5)

범위: 시드 카탈로그(pilot/core/all), 유사 모델 판정(HF_SIMILARITY_CRITERIA), revision pin +
manifest(에어갭/N2SF 근거), download plan 생성(실행 없음), 이벤트 스캔 주입 API.

| # | 케이스 | 방법 | 기대 |
|---|---|---|---|
| 1 | pilot 카탈로그 | `test_catalog_pilot_matches_script` | 12모델 — 다운로드 스크립트와 동일 |
| 2 | dedup·tier 규칙 | `test_catalog_dedup_and_tiers` | 중복 model_id 최저 tier 유지, 잘못된 profile 거부 |
| 3 | family/param 추론 | `test_family_and_param_inference` | qwen/llama 추출, 7.8B 파싱, 무표기=None |
| 4 | 시드 멱등성 | `test_seed_idempotent` | 재시드 added=0 |
| 5 | pin + manifest | `test_pin_and_manifest` | pinned revision manifest 반영, 미등록 404 |
| 6 | download plan | `test_download_plan_command` | hf CLI 명령 + `--revision` + GGUF 제외 (실행 안 함) |
| 7 | 이벤트 스캔 유사판정 | `test_events_scan_similarity` | 유사=candidate(matched_to), 비유사/기등록=skip |
| 8 | 기준 커스텀 | `test_events_scan_custom_criteria_family_only` | family 단독 기준 동작 |
| 9 | 회귀+린트 | 전체 pytest + ruff | 기존 33건 포함 전건 통과 |
