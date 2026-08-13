# impl/30th — F10 RAG 기반 추가학습·모델 업그레이드

근거: PRD `.docs/SecuFTPL-PRD.md` F10(§3), §7.13.

## 범위

1. `POST /api/v1/rag/synthesize` — 텍스트 문서 목록 → 청킹 → cause/resolution 합성 QA 레코드
   생성 → 기존 게이트/검수 큐 편입(§7.3 재사용, 게이트 무우회 없음).
2. `POST /api/v1/rag/upload` — 문서 파일(PDF/DOCX/TXT/MD/HTML) 업로드 → 동일 합성(F3 텍스트
   추출 재사용).
3. `POST /api/v1/rag/upgrade` — 승인된 (RAG 합성 포함) 데이터셋으로 continual fine-tuning 잡
   제출. `continual_from_job_id`(선택, succeeded 잡만) 로 이어학습 기준 어댑터 참조 기록.
   §7.5 500건 게이트·F9 리소스 세부설정 동일 적용, 결과는 기존 리더보드(F1)에 나란히 등재.

## 시나리오

| # | 케이스 | 기대 결과 |
|---|---|---|
| 1 | 긴 텍스트 청킹(1900자, chunk_size=800) | 3개 청크, 각 ≤800자 |
| 2 | 빈 텍스트 청킹 | 빈 목록 |
| 3 | 합성 레코드 — LLM 미가용(결정적 폴백) | source_type=rag_synthesis, quality_grade=augmented, citations=[source] |
| 4 | `/rag/synthesize` 문서 1건 → 청크 N개 | ingest.queued == N |
| 5 | 빈 문서만 제출 | 422 |
| 6 | 미등록 모델로 `/rag/upgrade` | 422 |
| 7 | 합성→승인→베이스 잡→업그레이드 잡(continual_from_job_id=베이스) | 둘 다 리더보드에 등재 |
| 8 | 존재하지 않는 `continual_from_job_id` | 422, 사유에 필드명 포함 |

## 실행

`uv run pytest -q test/test_rag_upgrade.py -v` + 전체 회귀 `uv run pytest -q` + `uv run ruff check .`
