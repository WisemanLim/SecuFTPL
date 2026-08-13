# impl/24th 시험 시나리오 — 학습 워커 + 리더보드 상세

요구: ①리더보드 모델 선택 시 세부내용 ②튜닝 잡이 실제 학습을 진행(백그라운드 워커 미구현 결함).

| # | 케이스 | 방법 | 기대 |
|---|---|---|---|
| 1 | 백그라운드 학습 | `POST /tuning/jobs` → 폴링 | queued→running→succeeded, 어댑터 manifest 저장 |
| 2 | 학습 이벤트 | `GET /jobs/{id}/events` | train start·loss=·auto-eval·job succeeded 로그 |
| 3 | 자동 평가→리더보드 | 잡 완료 후 leaderboard | 해당 job_id 지표 반영 |
| 4 | 승인 0건 차단 | 잡 제출 | create_job 단계 422 (워커 진입 전) |
| 5 | 리더보드 상세 | `GET /leaderboard/detail/{model}` | 평가 이력 + 튜닝 잡, 미존재 404 |
| 6 | UI 상세 | /leaderboard 행 클릭 | 평가 이력·잡 표 패널 |
| 7 | UI 학습 폴링 | 위저드 ⑤ 잡 제출 | 손실 진행 표시, succeeded 시 자동 다음 |
| 8 | 실학습 전환 | torch 설치 시 | `_real_available()` → real 모드 (미설치=simulate) |
| 9 | 회귀+E2E | pytest+ruff+build+실기동 | 전건 통과 |
