# impl/30th 시험 결과 — F10 RAG 기반 추가학습·모델 업그레이드

- 일시: 2026-08-13
- 판정: **PASS**

| # | 케이스 | 결과 |
|---|---|---|
| 1 | 청킹(1900자→800 단위) | PASS — 3청크, 각 ≤800자 |
| 2 | 빈 텍스트 청킹 | PASS — 빈 목록 |
| 3 | 결정적 폴백 합성 | PASS — source_type/quality_grade/citations 확인 |
| 4 | `/rag/synthesize` 문서→청크→ingest | PASS |
| 5 | 빈 문서 제출 | PASS — 422 |
| 6 | 미등록 모델 업그레이드 | PASS — 422 |
| 7 | 합성→승인→베이스 잡→업그레이드(continual) | PASS — 둘 다 리더보드 등재 |
| 8 | 존재하지 않는 continual_from_job_id | PASS — 422 |
| 전체 | `uv run pytest -q` | PASS — 121 passed |
| 린트 | `uv run ruff check .` | PASS |

## 생성/수정 파일

- `app/services/rag_synth.py`(신규) — 청킹·cause/resolution 합성(결정적 폴백/Ollama 실합성)
- `app/api/rag.py`(신규) — `/api/v1/rag/synthesize`·`/upload`·`/upgrade`
- `app/models/tuning.py` — `TuningJobRow.continual_from_job_id` 컬럼
- `app/services/tuning.py` — `create_job`에 `continual_from_job_id` 검증(succeeded 잡만 참조 허용)
- `app/services/trainer.py` — continual 참조 이벤트 로그·매니페스트 기록
- `app/main.py` — `rag_router` 등록
- `test/test_rag_upgrade.py`(신규 8건)

## 잔여

- 파일 업로드(`/rag/upload`)는 단위 테스트 미포함(기존 F3 `extract_document_text` 재사용, 함수 자체는
  `test_records_*`에서 이미 검증됨) — 통합 시나리오는 다음 이터레이션에서 보강 가능
- RAG 벡터 검색/인덱스 자체는 Out of Scope(§3) — 본 구현은 "코퍼스→학습데이터 합성"까지만
