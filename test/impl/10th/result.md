# impl/10th 시험 결과 — E7 독립 frontend

- 일시: 2026-08-13
- 판정: **PASS** (6/6 — 빌드·서빙·프록시 E2E + 백엔드 회귀 65/65)

| # | 케이스 | 결과 |
|---|---|---|
| 1 | pnpm install | PASS |
| 2 | pnpm build | PASS — 6 라우트(/, /models, /datasets, /queue, /tuning, /leaderboard) |
| 3 | 페이지 서빙 | PASS — front:200, models-page:200 |
| 4 | API 프록시 | PASS — `/api/v1/models` → FastAPI JSON (rewrites, CORS 불요) |
| 5 | 백엔드 회귀 | PASS — pytest 65/65, ruff clean |
| 6 | 포트 SSOT | PASS — FRONT_PORT(.env.example), NEXT_PUBLIC_API_BASE(frontend/.env.local) |

## 수정·재시험 이력

1. `pnpm build` FAIL — pnpm 11 빌드스크립트 차단(`ERR_PNPM_IGNORED_BUILDS: sharp`).
   package.json `pnpm.onlyBuiltDependencies` → 무효(pnpm 10 방식),
   pnpm-workspace.yaml `onlyBuiltDependencies` → 무효 → **`allowBuilds: {sharp: true}`**(pnpm 11.10 방식) → PASS.

## 설계 노트

- **독립성(정정 반영)**: wise-FP frontend 는 구조(App Router·페이지 구성)만 참고 — 코드·의존 없음,
  (auth) 로그인 제외. SecuFTPL 워크스페이스 안에서 자체 빌드·배포.
- **프록시**: next.config.mjs rewrites 로 same-origin `/api/*` → FastAPI — CORS 미들웨어 불요,
  API 주소는 `NEXT_PUBLIC_API_BASE` 단일 키.
- 스타일: 표준(Tailwind) 대신 경량 전역 CSS — 디자인 시스템 델타는 `/wise-dev-standard:ui-design` 후속.
- Makefile: `front-install` / `front-dev` / `front-build`.
