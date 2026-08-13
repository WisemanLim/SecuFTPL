# impl/27th 시험 시나리오 — 튜닝 모니터링 + 모델 export

요구: ①running 진행률 실시간 ②잡 이벤트 히스토리 ③succeeded 모델 다운로드(export).

| # | 케이스 | 방법 | 기대 |
|---|---|---|---|
| 1 | 진행률 필드 | 잡 목록 `progress_pct/current_step/total_steps` | running 갱신, succeeded=100% |
| 2 | 실시간 폴링 | UI /tuning | running 잡 있으면 2초 주기 자동 새로고침 + 진행 바 |
| 3 | 이벤트 히스토리 | UI "히스토리" 버튼 → `/jobs/{id}/events` | 시각+메시지 로그 표시 |
| 4 | 모델 export | `GET /jobs/{id}/export` | succeeded=어댑터 tar.gz 스트리밍, 미완료/미존재=409/404 |
| 5 | UI 다운로드 | succeeded 행 "다운로드" | 브라우저 tar.gz 저장 |
| 6 | 회귀+E2E | pytest+ruff+build+실기동 | 전건 통과 |
