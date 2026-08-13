# impl/37th 시험 결과 — 잡 진행 실시간 스트리밍(WebSocket)

- 일시: 2026-08-13
- 판정: **PASS**

| # | 케이스 | 결과 |
|---|---|---|
| 1 | 존재하지 않는 job_id | PASS — `{"error":...}` + 정상 종료 |
| 2 | 이미 succeeded 인 job | PASS — 최종 스냅샷 후 종료 |
| 3 | 실서버(uvicorn) 직결(Node 네이티브 WebSocket) | **최초 FAIL → 수정 후 PASS** — `websocket.close()` 미호출로 `return` 시 비정상 종료(1006) 발생. `job not found`/종료 조건 두 지점에 `await websocket.close()` 추가로 해결. pytest `TestClient.websocket_connect`는 이 결함을 가려서 최초엔 2/2 PASS로 보였음(실 ASGI 프로토콜 차이) |
| 4 | Next.js rewrites 프록시 경유 연결 | PASS — 백엔드 직결과 동일 응답, WS 업그레이드가 프록시를 정상 통과 |
| 5 | `pnpm run build` | PASS — `/tuning` 포함 11개 라우트 정상 생성 |
| 전체 | `uv run pytest -q` | PASS — 130 passed(신규 2건 + 기존 128건 무변경) |
| 린트 | `uv run ruff check .` | PASS |

## 생성/수정 파일

- `app/api/tuning.py` — `WS /jobs/{id}/stream` 엔드포인트(+ `websocket.close()` 수정)
- `frontend/app/tuning/page.tsx` — running 잡별 WS 구독으로 실시간 진행률 반영(2초 폴링은
  신규 잡 발견용으로 병행 유지)
- `test/test_job_stream.py`(신규 2건)

## 교훈

- `pytest` + `TestClient.websocket_connect`는 실 uvicorn/ASGI 프로토콜의 일부 결함(close 핸드셰이크
  누락)을 가릴 수 있음 — WebSocket 기능은 **실 서버 기동 후 수동/스크립트 검증이 필수**임을 확인.
  이번엔 Node 네이티브 `WebSocket`으로 직결·Next.js 프록시 양쪽을 직접 연결해 발견·검증함.

## 잔여

- frontend 자동화 시험(Vitest/Playwright) 미배선, GGUF/MLX 실행, vLLM 양자화, 실학습 GPU 의존성,
  서빙 어댑터 실교체, 외부 큐(arq/celery, 다중 프로세스/노드 환경에서 필요) — 모두 신규 패키지/시스템
  설치가 필요해 사용자 승인 후 별도 이터레이션 권장
