# impl/22nd 시험 시나리오 — ⑥단계 지표 자동 채움 미동작

증상: 재진입 시 지표 미채움 + 구 UI 표시.

| # | 원인 후보 | 확인 | 조치 |
|---|---|---|---|
| 1 | **승인 레코드에 파싱 가능한 정답 없음** | 실DB `eval-template` → `count:0, skipped_unparsable:1` (승인분=문서 needs_annotation 뿐) | 무매칭 시 **기본 샘플 행 자동 채움** + 원인 안내 메시지 |
| 2 | 새로고침 시 위저드 상태 소실 | useState 만 사용 — 모델·잡·단계 리셋 | **sessionStorage 영속/복원** (STORE_KEY, 탭 단위) |
| 3 | 구 번들 표시 | 스크린샷 UI = 21차 이전 마크업 | 스택 재기동(local-restart) + "지표 자동 채우기" 수동 버튼 추가 |
| 4 | 회귀 | pytest + build | 전건 통과 |
