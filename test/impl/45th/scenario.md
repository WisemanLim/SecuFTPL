# impl/45th — E13 보안 벤치·평가 연동 (F16) (PRD v0.4, 2026-09-10)

Survey §3 P0+P1 반영(고도화 v0.4, 사용자 범위 승인). PRD 먼저 갱신 후 구현.

## 범위

- ctibench importer(질문+선택지+GT → canonical, task=cti_extraction)
- 평가 2축: `value_accuracy`(필드 값 정확도, 리스트 순서무시) 지표 추가
- `GET /datasets/export/lmeval-task` — lm-evaluation-harness 태스크 YAML
- 카탈로그: Foundation-Sec-8B-Instruct·Llama-Primus-Base·Lily-Cybersecurity(core)

## 시험

test/test_bench_eval.py 5건 + 전체 회귀 `uv run pytest` + `ruff check` + frontend(tsc·Vitest)
