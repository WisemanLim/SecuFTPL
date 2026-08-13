# impl/2nd 시험 시나리오 — 포트 SSOT (PRD §7.9 2026-08-13 추가)

결함: `LOCAL_INFRA=redis make local-all` 시 (a) PROC_MGR=pm2 기본값 미적용(honcho 기동),
(b) `Address already in use` — Procfile 이 `.env.local` 의 `API_PORT` 를 무시하고 8000 고정.

| # | 케이스 | 방법 | 기대 |
|---|---|---|---|
| 1 | PROC_MGR 기본 분기 | `make -n local-all` | pm2 분기 실행 (`ENV_FILE=.env.local npx pm2 start`) |
| 2 | honcho env 주입 | `.env.local` API_PORT=18400 → `make local-all PROC_MGR=honcho` → curl :18400/health | env 포트로 기동 |
| 3 | pm2 env 주입 | 동일 조건 `make local-all` (기본 pm2) → curl :18400/health + `make ps` | env 포트 기동, pm2 online |
| 4 | 정리·복원 | `make local-stop`, API_PORT=8000 복원, lsof :18400 | 잔여 프로세스 0 |
| 5 | 하드코딩 잔존 점검 | Procfile.dev / ecosystem.config.cjs / docker-compose.yml | 포트·IP 전부 `.env.*` 키 참조 |
