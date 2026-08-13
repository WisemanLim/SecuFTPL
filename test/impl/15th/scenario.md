# impl/15th 시험 시나리오 — 수집 채널 확장 (wise-FP Stage5 A/B/C 준용)

요구: 파일(멀티)·디렉토리·인터넷 수집 — wise-FP 데이터셋 기능 적용.

| # | 케이스 | 방법 | 기대 |
|---|---|---|---|
| 1 | 페이로드 파싱 | `test_parse_payload_jsonl_and_json` | JSONL·JSON 배열·단일 객체 |
| 2 | 정규화 | `test_normalize_records_autofills_record_id_and_defaults` | F6 변환 + record_id 해시 자동, 기본값 병합(레코드 명시값 우선) |
| 3 | 디렉토리(모드 B) | `test_collect_dir_glob_and_partial_errors` | glob 일괄, 파일별 부분 실패 리포트, 비디렉토리 오류 |
| 4 | URL 가드(모드 C) | `test_collect_url_whitelist_and_ssrf_guard` | 화이트리스트 외 거부·file: 스킴 거부·T3_untrusted 태깅 |
| 5 | 멀티 업로드 API(모드 A) | `test_upload_multi_files` | 정상 2 + 오류 1 파일 리포트, 전부 실패 시 422 |
| 6 | dir/url 엔드포인트 | `test_collect_dir_endpoint`·`test_collect_url_endpoint_rejects_non_whitelist` | queued 반영·422 |
| 7 | CLI | `secuftpl dataset collect-dir / collect-url` | 노출·동작 |
| 8 | 프론트 채널 UI + E2E | /datasets 채널 섹션·위저드 파일 업로드, 프록시 multipart 업로드 | queued=1 |
| 9 | 회귀 | pytest + ruff + build | 전건 통과 |
