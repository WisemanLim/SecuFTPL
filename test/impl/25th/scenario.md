# impl/25th 시험 시나리오 — 잡 후속처리 (재실행·삭제)

요구: queued/failed 중단 잡에 대해 재실행·삭제 등 후속처리.

| # | 케이스 | 방법 | 기대 |
|---|---|---|---|
| 1 | 재실행 차단 | succeeded 잡 `POST /jobs/{id}/retry` | 409 (queued/failed 만) |
| 2 | stuck 잡 재실행 | 워커 미투입 queued 잡 → retry | 백그라운드 재투입 → succeeded |
| 3 | 삭제 | `DELETE /jobs/{id}` | 이벤트 로그 연쇄 삭제, 재삭제 404 |
| 4 | running 보호 | (설계) running 잡 재실행/삭제 | 409 |
| 5 | UI | /tuning 잡 목록 | queued/failed=재실행 버튼, running 외=삭제(confirm) |
| 6 | 회귀+E2E | pytest+ruff+build+실기동 | 전건 통과 |
