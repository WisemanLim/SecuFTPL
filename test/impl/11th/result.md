# impl/11th 시험 결과 — 구동 통합

- 일시: 2026-08-13
- 판정: **PASS** (6/6, 수정·재시험 0회)

| # | 케이스 | 결과 |
|---|---|---|
| 1 | compose config (front 서비스) | PASS |
| 2 | pm2 `local-all` 일괄 기동 | PASS — web·front online, api:200 front:200 proxy:200 |
| 3 | `local-stop` 일괄 정리 | PASS — 8000/3000 리스너 0 |
| 4 | honcho 경로 | PASS — front:200, 정리 후 리스너 0 |
| 5 | FRONT_PORT 전 환경 SSOT | PASS — local/dev/staging=3000, prod=키만 |
| 6 | 백엔드 회귀 | PASS — pytest 65/65, ruff clean |

## 변경 요약

- **ecosystem.config.cjs**: `secuftpl-front` 앱 추가 — ENV_FILE 에서 FRONT_PORT 파싱,
  `NEXT_PUBLIC_API_BASE=http://{BIND_HOST}:{API_PORT}` 주입 (전부 env 참조, 하드코딩 없음)
- **Procfile.dev**: `front:` 프로세스 추가 (honcho 대안 경로 동일 동작)
- **docker-compose.yml**: `front` 서비스(profiles:[app]) — `frontend/Dockerfile` 빌드,
  컨테이너 내부 `NEXT_PUBLIC_API_BASE=http://api:8000`, 호스트 노출 `${FRONT_PORT}` →
  `make dev-all/staging-all/prod-all` 에 frontend 자동 포함
- **frontend/Dockerfile**: node:22-slim + corepack pnpm (스캐폴더 Node 템플릿 준용)
- **.env.***: FRONT_PORT 4개 환경 반영

## 비고

- `make dev`(단일 api 포그라운드)·`make front-dev`(단일 front)는 디버깅용으로 유지 —
  일괄 운용은 `make local-all`(host) / `make <env>-all`(컨테이너)이 표준 경로.
- front 컨테이너 이미지 실빌드는 `<env>-build` 시 수행(Dockerfile `|| true` 스텁 —
  구현 단계에서 `--frozen-lockfile` 강화 지점).
