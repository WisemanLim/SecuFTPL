# impl/33rd — Frontend: F9(리소스)·F11(다중런타임 export)·F12(평가지표 가이드) UI 연동

근거: PRD `.docs/SecuFTPL-PRD.md` F9·F11·F12. impl/29th~32nd 백엔드 구현 후 frontend 미연동
상태였음(README "다음 단계" 잔여). feature-keyword 미지정 — 백엔드 대비 UI 공백이 가장 큰
tuning/leaderboard 페이지를 이번 이터레이션 범위로 선정. F10(RAG 페이지)은 신규 페이지 규모라
다음 이터레이션으로 분리.

## 범위

1. `frontend/app/tuning/page.tsx`
   - 잡 제출 폼에 `max_gpu`/`max_vram_gb` 입력(F9, 미입력 시 서버 기본값)
   - 잡 목록에 리소스 한도 표시 컬럼
   - "리소스" 버튼 → `GET /jobs/{id}/resources` 결과(CPU/MEM/GPU) 출력
   - "다운로드" 버튼을 어댑터/풀모델로 분리(F11 `export?format=`), "GGUF 플랜"/"MLX 플랜" 버튼
     추가(`export-plan?target=`)
2. `frontend/app/leaderboard/page.tsx`
   - "평가지표 가이드·추천"(F12) 패널 — task_type·표본건수 선택 → `GET /eval-guide` 결과(추천
     지표·가이드 문구·신뢰도 안내) 표시

## 시나리오

| # | 케이스 | 기대 결과 |
|---|---|---|
| 1 | `pnpm run build`(타입체크 포함) | 컴파일 성공, 10개 라우트 정적 생성 |
| 2 | 백엔드 회귀(`uv run pytest -q`) | 121 passed (API 계약 변경 없음, 프런트만 소비) |
| 3 | 백엔드 기동 후 `GET /api/v1/tuning/eval-guide?task_type=alert_triage&case_count=10` 실호출 | 프런트 TS 타입과 필드명 일치(task_type/recommended_metrics/guide/case_count/reliability_note) |
| 4 | 코드 검토 — `/jobs/{id}/resources`·`/export-plan` 응답 필드명 vs TSX 타입 | limits/gpu_devices/command 등 일치 확인 |

## 실행

`cd frontend && pnpm run build` + 루트에서 `uv run pytest -q` + `uv run ruff check .` +
백엔드 임시 기동 후 curl 실호출 검증.
