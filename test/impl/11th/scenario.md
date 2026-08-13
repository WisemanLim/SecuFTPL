# impl/11th 시험 시나리오 — 구동 통합 (local-all = web+front, compose front 서비스)

요구: `make dev`/`make front-dev` 개별 구동 대신 `make local-all` 일괄 관리 +
ecosystem.config.cjs·dev/staging/prod 환경 반영.

| # | 케이스 | 방법 | 기대 |
|---|---|---|---|
| 1 | compose 구문 | `docker compose --env-file .env.dev --profile app config` | front 서비스 포함, 오류 없음 |
| 2 | pm2 일괄 기동 | `LOCAL_INFRA=redis make local-all` → curl api/front/proxy | secuftpl-web·secuftpl-front online, 3응답 200 |
| 3 | 일괄 정리 | `make local-stop` → lsof 8000/3000 | 리스너 0 |
| 4 | honcho 경로 | `PROC_MGR=honcho make local-all` → curl front | web+front 기동, 200, 정리 후 리스너 0 |
| 5 | 포트 SSOT | FRONT_PORT: .env.{local,dev,staging}=3000 / .env.prod=키만 | 전 환경 반영, ecosystem·Procfile·compose 가 env 참조 |
| 6 | 백엔드 회귀 | pytest + ruff | 65건 전건 통과 |
