# impl/5th 시험 결과

- 일시: 2026-08-13
- 판정: **PASS** (pytest 47/47 — 신규 6 + 회귀 41, ruff 0 오류, `secuftpl --help` 동작)

| # | 케이스 | 결과 |
|---|---|---|
| 1~5 | CLI (dataset·models 전 명령) | PASS — in-memory sqlite 격리(전역 engine monkeypatch) |
| 6 | Supervisor UI 서빙 | PASS |
| 7 | 엔트리포인트 | PASS (`[project.scripts] secuftpl = "app.cli:app"`) |
| 8 | 회귀+린트 | PASS (ruff B008 은 app/cli.py 한정 typer 관용구 예외 처리) |

## 설계 노트

- **CLI = DB 직접 접근**: API 서버 불필요(F8 요구 — frontend 부재 환경). API 핸들러 함수 재사용으로
  UI/CLI/HTTP 세 경로가 동일 로직 공유.
- **Supervisor UI = 경량 내장**(가정 명시): FastAPI FileResponse 단일 HTML, 빌드체인·로그인 없음.
  wise-FP frontend 의 모델선택→용도→데이터셋 흐름 준용. **내부망 전용**(BIND_HOST=127.0.0.1) —
  외부 노출 시 인증 게이트웨이 필수. Next.js 본편은 E7.
- 튜닝 잡 제출 버튼은 E3 완성 시 활성화(비활성 + 안내 표기).
