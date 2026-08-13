# impl/2nd 시험 결과

- 일시: 2026-08-13
- 판정: **PASS** (5/5)

| # | 케이스 | 결과 |
|---|---|---|
| 1 | PROC_MGR 기본 분기 | PASS — `ENV_FILE=.env.local npx pm2 start ecosystem.config.cjs` |
| 2 | honcho env 주입 (API_PORT=18400) | PASS — `{"status":"ok","env":"local"}` @18400 |
| 3 | pm2 env 주입 (기본 경로) | PASS — secuftpl-web online, @18400 응답 |
| 4 | 정리·복원 | PASS — local-stop 후 리스너 0, API_PORT=8000 복원 |
| 5 | 하드코딩 잔존 | PASS — Procfile `${BIND_HOST}/${API_PORT}`, ecosystem=ENV_FILE 파싱, compose=기존 env 참조 |

## 근본 원인·수정

1. **make 인라인 주석 함정**: `PROC_MGR ?= pm2   # 주석` — 주석 앞 trailing space 가 값에 포함되어
   `ifeq ($(PROC_MGR),pm2)` 불일치 → 항상 honcho 분기. → 주석 별도 줄로 이동.
2. **포트 하드코딩**: Procfile `${PORT:-8000}`(API_PORT 아님) + honcho 가 `.env.local` 미로드,
   ecosystem.config.cjs 8000 고정. → Makefile `HONCHO`에 `-e .env.$(ENV)`, `PM2`에 `ENV_FILE=.env.$(ENV)`,
   Procfile `${BIND_HOST:-127.0.0.1}/${API_PORT:-8000}`, ecosystem 은 ENV_FILE 파서로 동적 로드.

## 비고

- 사용자 보고 시점의 8000/6379 점유 프로세스는 재현 시점에 이미 종료(lsof 0건) — 이후 충돌은
  `.env.<env>` 의 `API_PORT` 변경만으로 해결 가능(포트 SSOT, PRD §7.9).
