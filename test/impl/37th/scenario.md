# impl/37th — 잡 진행 실시간 스트리밍(WebSocket)

근거: PRD `.docs/SecuFTPL-PRD.md` F9(§7.12 실시간 모니터링), README 잔여 항목
"장시간 잡용 외부 큐(arq/celery)·WebSocket 진행 스트리밍". feature-keyword 미지정 —
남은 backend 항목(GGUF/MLX 실행, vLLM 양자화, torch/transformers/peft/trl 실학습, frontend
Vitest 배선)은 모두 신규 패키지 설치 승인이 필요해 보류. WebSocket 은 FastAPI/uvicorn[standard]에
이미 포함된 `websockets` 패키지로 신규 설치 없이 구현 가능해 이번 범위로 선정.

## 범위

1. `app/api/tuning.py` — `WS /api/v1/tuning/jobs/{id}/stream` 신설. 0.3초 주기로 상태·진행률·
   신규 이벤트를 push, `succeeded`/`failed` 도달 시 마지막 스냅샷 전송 후 정상 종료(`websocket.close()`).
   기존 폴링 엔드포인트(`GET /events`)는 유지(대안 제공, 하드 게이트 아님).
2. `frontend/app/tuning/page.tsx` — running 잡마다 WS 구독해 진행률을 즉시 반영. 기존 2초
   폴링은 "다른 세션/배치가 만든 신규 잡 발견"용으로 유지(용도 분리, surgical 변경).

## 시나리오

| # | 케이스 | 기대 결과 |
|---|---|---|
| 1 | 존재하지 않는 job_id 로 WS 연결 | `{"error": "..."}` 전송 후 정상 종료(1000) |
| 2 | 이미 succeeded 인 job 으로 WS 연결 | 최종 스냅샷(status/progress_pct=100/new_events) 전송 후 종료 |
| 3 | (수동) uvicorn 실서버 + Node 네이티브 WebSocket 클라이언트로 직결 | 정상 메시지 수신·정상 종료(1000) — pytest `TestClient.websocket_connect`가 가리는 실 프로토콜 결함(초기엔 1006) 발견·수정 |
| 4 | (수동) 같은 클라이언트로 Next.js `rewrites()` 프록시(포트 상이) 경유 연결 | 백엔드 직결과 동일 결과 — WS 업그레이드가 프록시를 통과함을 확인 |
| 5 | `pnpm run build` | 컴파일·타입체크 성공 |
| 6 | 전체 회귀 | 기존 128건 무변경 통과 |

## 실행

`uv run pytest -q test/test_job_stream.py -v` + 전체 회귀 `uv run pytest -q` + `uv run ruff check .` +
`cd frontend && pnpm run build` + 수동: 백엔드(uvicorn)·프런트(`next dev`) 임시 기동 후 Node
네이티브 `WebSocket`으로 직결/프록시 양쪽 연결 검증(케이스 3·4, pytest 로는 프록시 경로가
검증되지 않으므로 별도 수동 확인 필수).
