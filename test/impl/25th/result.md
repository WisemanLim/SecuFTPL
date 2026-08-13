# impl/25th 시험 결과 — 잡 후속처리

- 일시: 2026-08-13
- 판정: **PASS** (pytest 91/91 — 신규 2, ruff clean, 빌드 OK, E2E retry 409·delete)

| # | 케이스 | 결과 |
|---|---|---|
| 1 | succeeded 재실행 차단 | PASS 409 |
| 2 | stuck queued 재실행 → succeeded | PASS |
| 3 | 삭제 + 이벤트 연쇄 + 재삭제 404 | PASS |
| 4 | running 보호 | 구현(409) |
| 5 | UI 재실행/삭제 버튼 | 코드 반영 |
| 6 | E2E | PASS — retry(succeeded)=409, delete=deleted |

## 원인 (스크린샷의 다수 queued)

24차 이전(워커 미구현 시절) 생성된 잡 + 서버 재기동으로 BackgroundTask 소실된 잡이
queued 로 정체 — 실행도 정리도 불가했음.

## 구현

- `POST /tuning/jobs/{id}/retry` — queued/failed 만 재실행(status 초기화 + 에러 클리어 →
  백그라운드 워커 재투입). running/succeeded 는 409.
- `DELETE /tuning/jobs/{id}` — 잡 + 이벤트 로그 연쇄 삭제. running 은 409. 평가 결과는 이력 유지.
- UI(/tuning): queued/failed 행에 **재실행**, running 외 행에 **삭제**(confirm 팝업).

## 비고

- 서버 재기동 시 running→중단 잡은 다음 기동에서 여전히 running 표기될 수 있음 —
  재실행 대상(queued/failed)이 아니므로, 필요 시 삭제(running 아님 확인 후) 또는
  향후 기동 시 stale running 리셋 훅은 확장 지점.
