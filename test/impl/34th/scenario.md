# impl/34th — Frontend: F10 RAG 페이지(신규)

근거: PRD `.docs/SecuFTPL-PRD.md` F10(§3), §7.13. impl/33rd README 잔여 항목 "frontend F10 RAG
페이지"를 이번 이터레이션 범위로 선정(feature-keyword 미지정, 남은 백엔드-프런트 공백 중 최대).

## 범위

1. `frontend/app/rag/page.tsx`(신규) — ①RAG 코퍼스 합성(텍스트 직접입력 다건 추가 + 문서파일
   업로드, `/rag/synthesize`·`/rag/upload`) ②모델 업그레이드(모델·데이터셋버전·
   `continual_from_job_id`(succeeded 잡 목록에서 선택)·리소스(max_gpu/max_vram_gb) 제출,
   `/rag/upgrade`).
2. `frontend/components/Shell.tsx` — 사이드바에 "RAG 업그레이드" 내비게이션 항목 추가.

## 시나리오

| # | 케이스 | 기대 결과 |
|---|---|---|
| 1 | `pnpm run build`(타입체크 포함) | 컴파일 성공, 11개 라우트(`/rag` 포함) 정적 생성 |
| 2 | 백엔드 회귀(`uv run pytest -q`) | 121 passed (API 계약 무변경) |
| 3 | 백엔드 임시 기동 + `curl /api/v1/rag/synthesize`(텍스트 1건) | TSX `synthesizeText` 사용 필드(documents/chunks/ingest.queued)와 응답 일치 |
| 4 | 백엔드 임시 기동 + `curl "/api/v1/tuning/jobs?status=succeeded"` | TSX `loadModelsAndJobs`(continual 후보 목록) 사용 필드(count/jobs[])와 응답 일치 |

## 실행

`cd frontend && pnpm run build` + 루트에서 `uv run pytest -q` + `uv run ruff check .` +
백엔드 임시 기동 후 curl 실호출 검증.
