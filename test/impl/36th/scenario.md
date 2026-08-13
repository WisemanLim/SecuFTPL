# impl/36th — ops cron 배선 (야간 배치·HF polling crontab 플랜)

근거: PRD `.docs/SecuFTPL-PRD.md` F5·F2(§7.5·§7.9). feature-keyword 미지정 — README 잔여
항목 중 새 네트워크 설치가 필요 없는 유일한 backend 항목("ops cron 배선")을 선정
(GGUF/MLX 실행·vLLM 양자화·frontend Vitest 배선은 신규 패키지 설치 승인 필요해 보류).

## 범위

1. `app/core/config.py` — `ft_trigger_schedule_cron`·`hf_polling_cron` 설정 추가(기존
   `.env.example`의 값과 동일 기본값, 지금까지 app이 읽지 않던 순수 문서값이었음).
2. `app/services/ops_cron.py`(신규) — `cron_plan(base_url)`: 야간 배치(F5)·HF 신규 모델
   polling(F2) crontab 라인 생성. `model_download.download_plan`·`export_runtime.conversion_plan`
   과 동일 원칙 — **생성만, 설치/실행 없음**.
3. `app/api/batch.py` — `GET /api/v1/batch/cron-plan?base_url=` 신설.
4. `app/cli.py` — `secuftpl batch cron-plan [--base-url]` 신설.
5. `frontend/app/tuning/page.tsx` — "야간 배치" 패널에 "ops cron 플랜" 버튼 추가.

## 시나리오

| # | 케이스 | 기대 결과 |
|---|---|---|
| 1 | `cron_plan()` 기본 호출 | 두 크론표현식·두 엔드포인트 경로·"crontab -e" 안내 포함 |
| 2 | trailing slash 있는 base_url | 이중 슬래시 없이 정규화 |
| 3 | `GET /api/v1/batch/cron-plan`(기본/커스텀 base_url) | 응답 `command`에 커스텀 base_url 반영 |
| 4 | `secuftpl batch cron-plan` CLI | 동일 플랜 텍스트 stdout 출력 |
| 5 | `pnpm run build`(frontend) | 컴파일·타입체크 성공 |
| 6 | 전체 회귀 | 기존 125건 무변경 통과 |

## 실행

`uv run pytest -q test/test_ops_cron.py -v` + 전체 회귀 `uv run pytest -q` + `uv run ruff check .` +
`cd frontend && pnpm run build` + 백엔드 임시 기동 후 curl/CLI 실호출 검증.
