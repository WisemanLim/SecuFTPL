# impl/26th 시험 시나리오 — 리더보드 상세 잡 액션 + 평가 결과 삭제

요구: ①리더보드 상세 패널 튜닝 잡(7) 표에도 재실행/삭제 ②평가 리더보드 평가 결과 삭제.

| # | 케이스 | 방법 | 기대 |
|---|---|---|---|
| 1 | 평가 삭제 API | `DELETE /tuning/leaderboard/{eval_id}` | 평가 1건 삭제 → 리더보드에서 제거, 재삭제 404 |
| 2 | detail eval_id | `GET /leaderboard/detail/{model}` | evaluations 에 eval_id 포함(삭제용) |
| 3 | UI 평가 삭제 | 상세 평가 이력 행 액션 | confirm → delEval → 목록·상세 갱신 |
| 4 | UI 잡 재실행/삭제 | 상세 튜닝 잡 표 액션 | queued/failed=재실행, running 외=삭제(25차 API 재사용) |
| 5 | 회귀+빌드 | pytest+ruff+build | 전건 통과 |
