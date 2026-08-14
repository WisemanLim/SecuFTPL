# impl/41st 결과 — F13·F14·F15 (2026-08-14)

## 판정: PASS

| # | 케이스 | 결과 |
|---|---|---|
| 1 | 출처 없는 레코드 ingest 거부 | PASS — `test_ingest_rejects_missing_attribution` |
| 2 | 업로드 채널 자동 스탬핑 | PASS — `test_upload_channel_auto_stamps_attribution` |
| 3 | 검수 큐 출처 노출 | PASS — `test_queue_exposes_source_uri` |
| 4 | export approved JSONL | PASS — `test_export_jsonl_approved_only` |
| 5 | export zip+manifest·sha256 일치 | PASS — `test_export_zip_with_manifest_sources_and_hash` |
| 6 | export 422/404·manifest 미리보기 | PASS — `test_export_manifest_preview_and_errors` |
| 7 | run 기록·집계·채널 필터 | PASS — `test_ingest_records_pipeline_run`, `test_runs_channel_filter_and_404` |
| 8 | CLI export 실 DB | PASS — 1000건 + manifest 생성 (스모크) |
| 9 | CLI export `--input` | PASS — 파일 입력 → alpaca 1000건 + manifest (스모크) |
| 10 | CLI backfill dry-run | PASS — 레거시 1000건 감지, DB 무변경 |
| 11 | backend 회귀 | PASS — `uv run pytest` **144 passed**, `ruff check` clean |
| 12 | frontend 회귀 | PASS — Vitest **7 passed**, `tsc --noEmit` clean |

## 발견·수정 사항

- 신규 게이트 ③ 도입으로 기존 테스트 픽스처 12개 파일이 출처 필드 미포함 →
  `source_uri`/`source_hash_sha256` 추가(의도된 파괴적 변경, PRD F14).
- `test_ingest_blocks_schema_error_and_exact_dup` — 출처 없는 불량 레코드는 이제
  스키마 검증보다 게이트 ③이 먼저 차단(`rejected_attribution`)하도록 기대값 갱신.
- 저장 payload 에 `license` 가 스키마 기본값으로만 존재(미기록) → ingest 시
  `license`·`ingested_at` 명기(스탬핑)로 수정 — manifest 출처 집계 정확성 확보.
- `content_hash` 는 messages 텍스트만 해싱 → `ingested_at` 스탬핑이 중복제거에 영향 없음 확인.
- 실 DB(local.db) 레거시 1000건 출처 누락 확인 — 운영 반영 시
  `secuftpl dataset backfill-attribution --apply` 1회 실행 필요(검수 상태 유지, `legacy:unknown`).

## 잔여

- 게이트 ②(주입 탐지)·⑧(split) run 통계는 현 파이프라인 구조상 게이트 ④⑦과 통합 집계 —
  단계 개별 분리는 후속 이터레이션 후보.
- Supervisor 경량 UI(/supervisor)에는 다운로드 버튼 미추가(본편 frontend 만) — 필요 시 후속.
