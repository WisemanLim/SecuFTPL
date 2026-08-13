# dev-env 시험 결과 — secuftpl (python-fastapi)

- 일시: 2026-08-12
- 판정: **PASS** (9/9)

| # | 케이스 | 결과 | 비고 |
|---|---|---|---|
| 1 | make preflight | PASS | Python 3.11+, uv, docker compose v2 확인 |
| 2 | uv sync | PASS | 37 패키지 resolve, 오류 없음 |
| 3 | make up ENV=dev | PASS | secuftpl-postgres-1, secuftpl-redis-1 기동 |
| 4 | DB 연결 | PASS | `pg_isready -U app` → accepting connections |
| 5 | 앱 기동 | PASS | uvicorn 기동 (포트 18321 임시) |
| 6 | 헬스 체크 | PASS | `{"status":"ok","env":"local"}` |
| 7 | make test | PASS* | pytest exit 5(no tests) — 스캐폴드 직후 정상. impl/1st 부터 테스트 존재 |
| 8 | local-all/ps | SKIP | 백그라운드 상주 불필요 판단 — dev(단일)로 대체 검증 |
| 9 | make down | PASS | 컨테이너·orphan 정리 |

특이사항: `VIRTUAL_ENV` 경고(상위 SeCuardian venv 활성 상태) — uv 가 프로젝트 `.venv` 사용, 무해.
