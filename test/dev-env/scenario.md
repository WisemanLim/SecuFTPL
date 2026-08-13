# dev-env 검증 시나리오 — secuftpl (python-fastapi)

표준 환경이 동작하는지 1회 검증. 결과는 `logs/` 에 저장(비커밋).

| # | 케이스 | 명령 | 기대 결과 |
|---|---|---|---|
| 1 | 사전 호환성 | `make preflight` | Preflight OK (Python 3.11+, uv, docker compose v2) |
| 2 | 의존성 설치 | `uv sync` | uv.lock 생성, 오류 없음 |
| 3 | infra 기동 | `make up ENV=dev` | postgres(healthy) + redis 기동 |
| 4 | DB 연결 | `psql postgresql://app:***@localhost:5432/secuftpl -c 'select 1'` | `1` 반환 |
| 5 | 앱 기동 | `make dev` | uvicorn --reload 기동 |
| 6 | 헬스 체크 | `curl http://127.0.0.1:8000/health` | `{"status":"ok","env":"local"}` |
| 7 | 테스트 러너 | `make test` | pytest 수집·실행 (초기 0건 통과 허용) |
| 8 | 멀티프로세스 | `LOCAL_INFRA=redis make local-all && make ps && make local-stop` | honcho 백그라운드 기동·검증·정리 |
| 9 | 정리 | `make down` | 컨테이너·orphan 제거 |
