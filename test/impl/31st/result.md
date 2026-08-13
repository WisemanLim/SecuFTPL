# impl/31st 시험 결과 — F11 다중 런타임 배포·풀모델 export

- 일시: 2026-08-13
- 판정: **PASS**

| # | 케이스 | 결과 |
|---|---|---|
| 1 | `merge_full_model` 시뮬레이션(peft 미설치) | PASS — mode=simulated, manifest 생성 |
| 2 | `conversion_plan(..., "gguf")` | PASS |
| 3 | `conversion_plan(..., "mlx")` | PASS |
| 4 | 미지원 target | PASS — ValueError |
| 5 | `GET .../export`(adapter 기본) | PASS — 200, tar.gz |
| 6 | `GET .../export?format=full` | PASS — 200, merge 자동 트리거 |
| 7 | `GET .../export?format=onnx` | PASS — 422 |
| 8 | `GET .../export-plan?target=gguf\|mlx` | PASS |
| 9 | 존재하지 않는 job export-plan | PASS — 404 |
| 전체 | `uv run pytest -q` | PASS — 121 passed |
| 린트 | `uv run ruff check .` | PASS |

## 생성/수정 파일

- `app/services/export_runtime.py`(신규) — merge(real/simulate)·GGUF/MLX 변환 플랜(실행 없음)
- `app/api/tuning.py` — `export_model`에 `format=adapter\|full` 추가, `export_plan` 엔드포인트 신설
- `test/test_export_runtime.py`(신규 9건)

## 잔여

- 실제 GGUF/MLX 바이너리 변환은 llama.cpp/mlx_lm 설치 환경에서 사용자가 플랜 명령을 직접 실행
  (네트워크/빌드 도구 설치는 사용자 승인 후 — PRD 규칙 준수)
- vLLM/AWQ·GPTQ 양자화는 별도 확장 지점(§7.14 표에 문서화, 미구현)
