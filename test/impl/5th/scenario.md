# impl/5th 시험 시나리오 — E8: Supervisor 시험 UI(F7) + 파이프라인 CLI(F8)

범위(PRD §7.10, 2026-08-13 추가): 경량 내장 Supervisor UI(`/supervisor`) + `secuftpl` CLI.

| # | 케이스 | 방법 | 기대 |
|---|---|---|---|
| 1 | CLI validate 종료코드 | `test_cli_dataset_validate_pass_and_fail` | 통과=0, invalid 존재=1 (배치 게이트 스크립팅) |
| 2 | CLI convert 파일 출력 | `test_cli_dataset_convert_to_file` | alpaca→canonical JSONL 파일 생성 |
| 3 | CLI ingest→queue→review | `test_cli_ingest_queue_review_flow` | API 서버 없이 DB 직접 파이프라인 완주 |
| 4 | CLI models 시드→pin→manifest→plan | `test_cli_models_seed_pin_manifest_plan` | pilot 12 시드, pin/manifest 반영, hf 명령 생성, 미등록 exit 1 |
| 5 | CLI 이벤트 스캔 | `test_cli_models_scan` | JSONL 주입 → candidate 판정 |
| 6 | Supervisor UI 서빙 | `test_supervisor_page_served` | 200 + ①모델선택/②사용용도/④검수큐/API 경로 마커 |
| 7 | 엔트리포인트 | `uv run secuftpl --help` | typer 앱 노출 |
| 8 | 회귀+린트 | 전체 pytest + ruff | 기존 41건 포함 전건 통과 |
