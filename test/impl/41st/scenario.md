# impl/41st — F13 데이터셋 다운로드 · F14 출처 필수화 · F15 파이프라인 run 추적 (PRD v0.3 §7.15, E12)

인자: "데이터셋 기능 확장 — (1) 수집/문서(개별·디렉토리) 기반 데이터셋 구성 결과 다운로드,
(2) 수집 시 출처 필수 명기, (3) 수집·정제 상세 파이프라인 구성. 추가: CLI 별도 데이터셋
파일 입력 옵션(--input)."

PRD v0.3 갱신(F13~F15 신규 스코프, §7.15, E12) 후 구현(step 4 준수).

## 범위

- **F14 출처 필수화**
  - `app/services/gate.py` — 게이트 ③ `attribution_errors()`: `source_uri`·`source_hash_sha256`
    누락 레코드 반입 거부(`rejected_attribution`). license 는 저장 시 명기(기본값 의존 금지).
  - `app/services/collect.py` — `stamp_attribution()`: 채널별 자동 스탬핑
    (업로드=`upload://<파일명>`+파일 sha256, 디렉토리=파일 `file://` URI, URL=요청 URL+응답 sha256).
  - `app/api/feedback.py` — 환류 레코드 `assistant://<모델>/<rid>` + 원문 sha256 스탬핑.
  - `app/services/rag_synth.py` — 합성 레코드에 청크 sha256 추가.
  - `app/api/records.py` — 검수 큐 목록에 `source_uri`/`license` 노출.
  - CLI `dataset backfill-attribution` — 기존 레코드 마이그레이션(dry-run 기본,
    `--apply` 시 `legacy:unknown` 태깅·검수 상태 유지).
- **F13 데이터셋 다운로드**
  - `app/services/dataset_export.py`(신규) — 포맷 변환 JSONL 직렬화 + manifest
    (건수·task_type/quality_grade/source_type 분포·출처별 집계·파일 sha256) + zip 패키징.
  - `GET /api/v1/datasets/export` (format/review_state/dataset_version/with_manifest),
    `GET /api/v1/datasets/export/manifest` (미리보기).
  - CLI `dataset export OUT [--format --review-state --dataset-version --with-manifest]`
    + **`--input FILE.jsonl`**(DB 대신 별도 파일 입력 — 사용자 추가 요구).
  - frontend datasets 페이지 ⑤ 다운로드 섹션(포맷·상태·manifest 선택), queue 페이지 출처 컬럼·상세 pill.
- **F15 run 추적**
  - `PipelineRunRow`(pipeline_runs 테이블) — ingest 1회=1 run, 단계별 통과/차단 건수·사유 샘플·출처 집계.
  - `GET /api/v1/datasets/runs`·`/runs/{run_id}`, CLI `dataset runs`.
  - 전 수집 경로 채널 태깅: api_ingest/file_upload/dir_collect/web_collect/augment/assistant_feedback/rag_synthesis.

## 시나리오

| # | 케이스 | 기대 결과 |
|---|---|---|
| 1 | 출처 없는 레코드 ingest | `rejected_attribution` + queued=0 (게이트 ③) |
| 2 | 파일 업로드(출처 미기재 원본) | 채널 자동 스탬핑 → queued, `upload://<파일명>` + sha256(64자) 확인 |
| 3 | 검수 큐 조회 | `source_uri`·`license` 필드 노출 |
| 4 | export 기본 호출 | approved 만 JSONL(x-ndjson) 다운로드 |
| 5 | export zip+manifest (alpaca) | zip 내 dataset.alpaca.jsonl+manifest.json, 출처별 집계·file_sha256 일치 |
| 6 | export 오류 | 미지원 포맷=422, 조건 불일치=404, manifest 미리보기 정상 |
| 7 | ingest run 기록 | run_id 반환, stats(total/queued/rejected_attribution/사유 샘플)·sources 집계, 채널 필터·404 |
| 8 | CLI export (실 DB) | 1000건 JSONL + manifest 생성 |
| 9 | CLI export `--input` (별도 파일) | DB 미접근, 파일 1000건 → alpaca 변환 + manifest |
| 10 | CLI backfill-attribution (dry-run) | 레거시 1000건 누락 감지, DB 무변경 |
| 11 | 전체 backend 회귀 | 기존 스위트 + 신규 9건 = 144건 전부 통과, ruff clean |
| 12 | frontend 회귀 | Vitest 7건 통과, `tsc --noEmit` clean |

## 실행

- `uv run pytest` (144건) / `uv run ruff check app test`
- `cd frontend && pnpm run test` / `npx tsc --noEmit`
- CLI: `dataset export`·`--input`·`backfill-attribution`(dry-run) 실 DB 스모크
