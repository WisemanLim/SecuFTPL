# impl/1st 시험 시나리오 — E1 데이터셋 코어 1차

범위(PRD Epic E1): canonical sft-messages 스키마 + 포맷 어댑터(F6) + 정제 게이트 검증부(§7.3 ④·⑦) + API.

| # | 케이스 | 방법 | 기대 |
|---|---|---|---|
| 1 | canonical 스키마 검증 | pytest `test_gate.py::test_valid_record_passes` 외 | 역할 규칙(마지막=assistant, user 필수)·metadata 필수 필드 강제 |
| 2 | 비밀값 스캐너 회귀 (COMPLIANCE) | `test_secret_detection_regression` | API_KEY/AWS/PRIVATE_KEY/JWT/SESSION_COOKIE 5패턴 전부 탐지 |
| 3 | 내부자산 탐지 | `test_internal_asset_detection` | 내부IP·호스트명·사내메일 탐지 |
| 4 | 프롬프트 주입 탐지 (게이트 ②) | `test_prompt_injection_detection` | ko/en 주입 문구 탐지 |
| 5 | 배치 검증 리포트 | `test_batch_report` | total/valid/invalid/details 형식 |
| 6 | alpaca 왕복 변환 | `test_formats.py::test_alpaca_roundtrip` | canonical 경유 무손실 |
| 7 | sharegpt 왕복 변환 | `test_sharegpt_roundtrip` | role 매핑 정확, 원본 복원 |
| 8 | 교차 변환 | `test_cross_format_alpaca_to_openai_chat` | alpaca→openai-chat |
| 9 | 미지원 포맷 오류 | `test_unsupported_format_raises` | ValueError → API 422 |
| 10 | API 엔드포인트 | `test_api.py` | /formats, /validate, /convert + 오류 422 |
| 11 | 만족도 스키마 (§7.9) | `test_satisfaction_binary_and_likert5` | binary=up/down, likert5=1~5, 교차 입력 거부 |
| 12 | 린트 | `uv run ruff check .` | 0 오류 |
