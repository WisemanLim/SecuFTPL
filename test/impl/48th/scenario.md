# impl/48th — E16 학습 고도화 (F19) (PRD v0.4, 2026-09-10)

Survey §3 P0+P1 반영(고도화 v0.4, 사용자 범위 승인). PRD 먼저 갱신 후 구현.

## 범위

- train_plan `lora_variant`(lora/rslora/dora — use_rslora/use_dora 플래그, 근거 arXiv 주석)
- `GET /tuning/jobs/{id}/train-plan/mlx` — mlx-lm LoRA 실학습 명령 플랜(available 플래그, 실행은 worker/수동)

## 시험

test/test_lora_variants.py 2건 + 전체 회귀 `uv run pytest` + `ruff check` + frontend(tsc·Vitest)
