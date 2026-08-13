# impl/31st — F11 다중 런타임 배포·풀모델 export

근거: PRD `.docs/SecuFTPL-PRD.md` F11(§3), §7.14.

## 범위

1. `GET /jobs/{id}/export?format=adapter|full` — 기존 어댑터 export(default)에 `full`(어댑터
   merge → 풀모델) 옵션 추가. real(peft 설치 시 merge_and_unload) / simulate(매니페스트만) 자동 선택.
2. `GET /jobs/{id}/export-plan?target=gguf|mlx` — Ollama/llama.cpp(GGUF)·MLX 변환 명령 플랜
   생성(실행 없음, `download_plan` 과 동일 원칙).

## 시나리오

| # | 케이스 | 기대 결과 |
|---|---|---|
| 1 | `merge_full_model` (peft 미설치 환경) | mode=simulated, export_manifest.json 생성 |
| 2 | `conversion_plan(..., "gguf")` | convert_hf_to_gguf.py + q4_k_m 프리셋 포함 |
| 3 | `conversion_plan(..., "mlx")` | mlx_lm.convert 포함 |
| 4 | 미지원 target | ValueError |
| 5 | `GET .../export`(기본) | 200, `{job_id}.tar.gz` |
| 6 | `GET .../export?format=full` | 200, `{job_id}-full.tar.gz`(merge 자동 트리거) |
| 7 | `GET .../export?format=onnx` | 422 |
| 8 | `GET .../export-plan?target=gguf\|mlx` | command 필드에 변환 명령 포함 |
| 9 | 존재하지 않는 job의 export-plan | 404 |

## 실행

`uv run pytest -q test/test_export_runtime.py -v` + 전체 회귀 `uv run pytest -q` + `uv run ruff check .`
