# impl/38th 시험 결과 — frontend Vitest/Playwright + F11 실 MLX export + GPU 가이드

- 일시: 2026-08-13
- 판정: **PASS**

| # | 케이스 | 결과 |
|---|---|---|
| 1 | `mlx-lm` 설치 후 real/merge availability | PASS — 둘 다 False, 기존 130건 영향 없음 확인 |
| 2 | `convert_to_mlx` 시뮬 매니페스트 입력 | PASS — FileNotFoundError |
| 3 | `convert_to_mlx` 실 테스트 모델(로컬 스냅샷) | PASS — 실제 MLX `model.safetensors`·`config.json` 등 생성 확인 |
| 4 | `POST .../export/mlx`(시뮬 merge) | PASS — 422 |
| 5 | `POST .../export/mlx`(존재하지 않는 잡) | PASS — 404 |
| 6 | frontend Vitest | PASS — 3 files / 7 tests |
| 7 | frontend Playwright e2e | PASS — 2 tests(백엔드 미기동 허용) |
| 8 | `pnpm run build` | PASS — 9개 라우트 정상 생성 |
| 9 | backend 전체 회귀 | PASS — 133 passed |
| 린트 | `uv run ruff check .` | PASS |

## 생성/수정 파일

**MLX 실 export (F11)**
- `pyproject.toml` — `[project.optional-dependencies] mlx = ["mlx-lm>=0.31"]`
- `app/services/export_runtime.py` — `_mlx_available`·`convert_to_mlx`
- `app/api/tuning.py` — `POST /jobs/{id}/export/mlx`
- `test/test_export_mlx_real.py`(신규 3건, mlx-lm 미설치 환경은 자동 skip)

**frontend 시험 배선**
- `frontend/package.json` — `vitest`·`@vitejs/plugin-react`·`jsdom`·`@testing-library/*`·
  `@playwright/test` devDependencies, `test`/`test:watch`/`test:e2e` 스크립트
- `frontend/vitest.config.mts`(신규), `frontend/playwright.config.ts`(신규)
- `frontend/test/setup.ts`·`lib_api.test.ts`·`lib_templates.test.ts`·`shell.test.tsx`(신규)
- `frontend/test/e2e/nav.spec.ts`(신규)
- `Makefile` — `front-test`·`front-test-e2e` 타겟
- `.gitignore` — `frontend/test-results/`·`playwright-report/`·`blob-report/`·`coverage/`

**GPU 배포 가이드**
- `.docs/GPU-실학습-배포-가이드.md`(신규) — vLLM·실 QLoRA·llama.cpp 별도 GPU 환경 절차 +
  torch/transformers/peft/trl 설치 시 테스트 스위트 위험 경고 및 선행 조치 권고

## 중요 발견 (설치 진행하지 않은 이유)

`app/services/trainer.py::_real_available()`는 `peft`·`torch`·`transformers`·`trl` import
가능 여부만으로 real/simulate 모드를 전환한다. 이 4개를 설치하면 **환경 구분 없이 즉시 실학습
모드로 전환**되어, 현재 133개 backend 테스트(전부 simulate 전제)가 깨질 위험이 있음을 발견했다.
GPU 워커에 이 패키지들을 설치하기 전에 `FORCE_TRAINING_MODE` 같은 명시적 플래그 도입을 선행
과제로 가이드에 기록했다(`.docs/GPU-실학습-배포-가이드.md` §2.2).

## 잔여

- vLLM, 실 QLoRA 학습(torch/transformers/peft/trl+bitsandbytes+CUDA), llama.cpp 실 GGUF 변환 —
  모두 GPU/Linux 환경에서 가이드 절차대로 별도 진행 필요(§2 참조)
