# impl/12th 시험 시나리오 — E7 UI 개편 (PRD §7.11)

요구 4건: ①브랜드 스타일(SeCuardian front 준용) ②좌측 접이식 사이드바 ③파이프라인 단계별
순차 자동 이동(이전 복귀 허용) ④스테퍼 상태 카드(단계별 진행 상태).

| # | 케이스 | 방법 | 기대 |
|---|---|---|---|
| 1 | 브랜드 팔레트 | globals.css 토큰 | Genians 그린(#86BC25 계열) — SeCuardian index.css @theme 준용, WCAG 대비 보정 |
| 2 | 사이드바 | Shell.tsx | 접기/펼치기 토글(localStorage 유지), 활성 메뉴 하이라이트, 접힘 시 아이콘만 |
| 3 | 위저드 8단계 | /pipeline | 모델→수집→검수→증강(스킵 가능)→튜닝→게이트→리더보드→배포 |
| 4 | 자동 다음 이동 | 수집 성공(queued>0)·잡 생성·게이트 passed | onOk 콜백에서 advance |
| 5 | 이전 복귀 | 완료/건너뜀 카드 클릭 | 해당 단계로 복귀(navigable), 진행 중/대기 카드는 비활성 |
| 6 | 스테퍼 상태 | Stepper.tsx | 완료=그린/진행=CI 원색/대기=회색/건너뜀=주황 헤더 카드 |
| 7 | 빌드·서빙 | pnpm build + local-all E2E | 8 라우트 빌드, /pipeline 200, 대시보드 CTA 노출 |
| 8 | 백엔드 회귀 | pytest + ruff | 65건 전건 통과 |
