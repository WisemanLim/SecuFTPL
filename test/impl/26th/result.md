# impl/26th 시험 결과 — 리더보드 상세 잡 액션 + 평가 결과 삭제

- 일시: 2026-08-13
- 판정: **PASS** (pytest 91/91 — 확장 1, ruff clean, 빌드 OK)

| # | 케이스 | 결과 |
|---|---|---|
| 1 | 평가 삭제 API + 404 | PASS (test_leaderboard_detail 확장) |
| 2 | detail eval_id 노출 | PASS |
| 3 | UI 평가 삭제 | 코드 반영 (confirm) |
| 4 | UI 잡 재실행/삭제 | 코드 반영 (25차 API 재사용) |
| 5 | 회귀+빌드 | PASS |

## 구현

- `DELETE /api/v1/tuning/leaderboard/{eval_id}` — 평가 결과 1건 삭제(잡·모델 유지).
- `leaderboard/detail` evaluations 에 `eval_id` 추가.
- UI(/leaderboard 상세 패널):
  - 평가 이력 표: 행별 **삭제**(confirm) → 평가 결과 제거 후 리더보드·상세 재로드.
  - 튜닝 잡 표: queued/failed=**재실행**, running 외=**삭제**(confirm) — 25차 잡 API 재사용.
  - 삭제/재실행 후 리더보드 목록 + 상세 패널 동시 갱신(refreshAll).

## 비고

25차는 /tuning 페이지 잡 목록에만 액션이 있었고, 사용자가 본 스크린샷은 리더보드 상세 패널이라
액션이 없었음 — 이번에 상세 패널에도 반영 + 평가 결과 삭제 신규.
