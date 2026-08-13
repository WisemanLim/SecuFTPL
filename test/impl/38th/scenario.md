# impl/38th — 남은 설치 승인 항목: frontend Vitest/Playwright + F11 실 MLX export

인자: "전부 신규 패키지/시스템 설치 필요 승인". 사전 조사 결과 이 머신(Apple Silicon, CUDA GPU 없음)
에서는 vLLM·실 QLoRA 학습(bitsandbytes 4bit)이 정상 동작 검증 불가 — 사용자에게 확인 후
"하드웨어에 맞는 것만 진행 + 나머지는 가이드 작성"으로 범위 확정.

## 범위

1. **frontend Vitest(단위) + Playwright(e2e) 배선** — 표준 프로파일(test-runner)이 요구하는
   시험 러너 공백 해소.
2. **F11 실 MLX export** — `mlx-lm`(Apple Silicon 네이티브, `torch`/`peft` 불필요 확인 후 설치) 로
   `export-plan`(명령 텍스트만)을 넘어 **실제 변환을 실행**하는 `POST /jobs/{id}/export/mlx` 신설.
3. **GPU 배포 가이드 문서화** — `.docs/GPU-실학습-배포-가이드.md`: vLLM·실 QLoRA·llama.cpp 실행을
   위한 별도 GPU 환경 절차 + 이번에 발견한 위험(2.2절: torch/transformers/peft/trl 설치 시
   `_real_available()` 가 즉시 True 로 전환되어 테스트 스위트가 깨질 수 있음) 경고.

## 시나리오

| # | 케이스 | 기대 결과 |
|---|---|---|
| 1 | `mlx-lm` 설치 후 `_real_available()`·`_merge_available()` | 여전히 False(torch/peft 미설치 확인됨 — 기존 133건 무영향) |
| 2 | `convert_to_mlx` — 시뮬레이션 매니페스트뿐인 폴더 | FileNotFoundError(정직한 실패, 가짜 성공 없음) |
| 3 | `convert_to_mlx` — **실 공개 테스트 모델**(로컬 스냅샷) | 실제 MLX 산출물(`model.safetensors` 등) 생성 확인(세션 임시 검증, 결과물 정리) |
| 4 | `POST /jobs/{id}/export/mlx` — succeeded 잡(시뮬 merge) | 422 (mlx 변환 실패 원인 그대로 노출) |
| 5 | `POST /jobs/{id}/export/mlx` — 존재하지 않는 잡 | 404 |
| 6 | frontend Vitest(`lib/api`·`lib/templates`·`Shell` 컴포넌트) | 7건 통과 |
| 7 | frontend Playwright e2e(사이드바 내비게이션·접기 상태 유지) | 2건 통과(백엔드 미기동 상태에서도 셸 정상 렌더) |
| 8 | `pnpm run build` | 컴파일·타입체크 성공 |
| 9 | 전체 backend 회귀 | 기존 130건 무변경 + 신규 3건(MLX) 통과 |

## 실행

`uv sync --extra mlx` → `uv run pytest -q` + `uv run ruff check .` →
`cd frontend && pnpm add -D vitest @vitejs/plugin-react jsdom @testing-library/react @testing-library/jest-dom @testing-library/dom && pnpm add -D @playwright/test && pnpm exec playwright install chromium` →
`pnpm run test` + `pnpm run test:e2e` + `pnpm run build`.
