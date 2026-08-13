# impl/10th 시험 시나리오 — E7: SecuFTPL 독립 frontend (2026-08-13 정정 반영)

범위: wise-FP frontend **참고만**(로그인 제외) — SecuFTPL `frontend/` 독립 Next.js 앱.
페이지: 대시보드·모델·데이터셋(용도/검증/수집/변환/증강)·검수 큐·튜닝(잡/배치)·리더보드.

| # | 케이스 | 방법 | 기대 |
|---|---|---|---|
| 1 | 의존성 설치 | `pnpm install` (Node 22·pnpm 11) | 성공 (sharp allowBuilds 승인) |
| 2 | 프로덕션 빌드 | `pnpm build` | 타입체크 포함 6 라우트 빌드 성공 |
| 3 | 페이지 서빙 | `pnpm start` → curl `/`, `/models` | 200 |
| 4 | API 프록시 | curl `:3300/api/v1/models` | rewrites 경유 FastAPI JSON 응답 (CORS 불요) |
| 5 | 백엔드 회귀 | 전체 pytest + ruff | 65건 전건 통과 |
| 6 | 포트 SSOT | FRONT_PORT env·rewrites NEXT_PUBLIC_API_BASE | .env 관리 (§7.9) |
