# GPU/CUDA 실학습·vLLM 배포 가이드

> 이 문서는 impl/38th(2026-08-13) 에서 "전부 신규 패키지/시스템 설치 승인" 요청에 대한 조사 결과다.
> 개발 머신(Apple Silicon, CUDA GPU 없음)에서는 vLLM·실 QLoRA 학습을 **정상 동작 검증할 수 없어**
> 여기 문서화만 하고, 하드웨어에 맞는 항목(frontend 시험, MLX 실 export)은 실제로 설치·구현·검증했다.

## 1. 이 세션에서 실제로 구현·검증한 것 (Apple Silicon)

| 항목 | 상태 | 근거 |
|---|---|---|
| frontend Vitest(단위) + Playwright(e2e) | ✅ 설치·구현·시험 통과 | `frontend/vitest.config.mts`, `frontend/playwright.config.ts`, `frontend/test/` |
| F11 실 MLX export(`mlx-lm`) | ✅ 설치·구현·**실 모델 변환으로 검증** | `app/services/export_runtime.py::convert_to_mlx`, `POST /jobs/{id}/export/mlx` |

### 1.1 frontend Vitest + Playwright

- devDependencies 는 이미 `frontend/package.json` 에 반영돼 있어 신규 clone 후 `pnpm install` 만으로
  Vitest 는 바로 실행 가능. Playwright 는 브라우저 바이너리를 별도 다운로드해야 한다:
  ```bash
  cd frontend
  pnpm install                          # vitest·@testing-library/*·@playwright/test 등
  pnpm exec playwright install chromium # 브라우저 바이너리(1회, ~270MB)
  ```
- 실행:
  ```bash
  make front-test       # 또는: cd frontend && pnpm run test        (Vitest 단위, 7건)
  make front-test-e2e   # 또는: cd frontend && pnpm run test:e2e    (Playwright e2e, 2건 — dev 서버 자동 기동)
  ```
- 구성 파일: `frontend/vitest.config.mts`(jsdom 환경, `test/**/*.test.{ts,tsx}` — `test/e2e/` 제외),
  `frontend/playwright.config.ts`(`test/e2e/` 전용, `webServer` 로 `pnpm dev` 자동 기동).
- 부작용 없음 확인: devDependencies 설치만으로 backend·기존 frontend 빌드에 영향 없음
  (별도 패키지 트리, `pnpm run build` 재확인 완료).

### 1.2 F11 MLX 실 export (`mlx-lm`)

- Apple Silicon 전용, 옵션 의존성으로 분리(`pyproject.toml` `[project.optional-dependencies] mlx`):
  ```bash
  uv sync --extra mlx   # mlx, mlx-lm, transformers 등 설치(torch/peft 는 설치되지 않음)
  ```
- **설치 전 안전성 확인**: `mlx-lm` 은 `transformers` 를 끌어오지만 `torch`/`peft`/`trl` 은 끌어오지
  않는다 — `_real_available()`(§2.2 참고)·`_merge_available()` 모두 여전히 `False` 를 반환해
  기존 133개 backend 테스트의 simulate 모드 동작에 **영향 없음**(설치 전 `uv pip install --dry-run
  mlx-lm` 으로 의존성 트리 확인 후 진행).
- 사용:
  ```bash
  curl -X POST localhost:8000/api/v1/tuning/jobs/<job_id>/export/mlx   # 실 변환 실행
  ```
  풀모델이 시뮬레이션 매니페스트뿐이면(peft/torch 미설치 상태) 422 로 실패 원인을 그대로 노출한다
  (§7.14) — real merge(§2.2 선행 조치 반영 후 peft/torch 설치 시)를 거친 실 HF 가중치를 입력해야
  실제 변환이 성공한다.
- 미설치 상태에서 호출하면 501(`mlx-lm 미설치 — 'uv sync --extra mlx' 후 재시도`)로 안내한다.

MLX 검증 방법(참고, 세션 임시 작업 — 결과물은 세션 종료 시 정리함): 공개 초소형 테스트 모델
(`hmellor/tiny-random-LlamaForCausalLM`, 실 Llama 아키텍처·수 MB)을 `huggingface_hub.snapshot_download`
로 완전히 받은 뒤 `mlx_lm.convert()` 로 실제 MLX 포맷 변환에 성공했다(`model.safetensors` 등 산출물
확인). 이후 로컬 디렉터리 입력으로도 동일하게 동작함을 재확인해, `merge_full_model`(§7.14, 실 merge)
결과물을 그대로 입력으로 넘기면 되는 구조임을 검증했다.

## 2. GPU(CUDA) 환경에서 별도로 진행해야 하는 것

### 2.1 vLLM

- vLLM은 주로 **Linux + NVIDIA CUDA** 대상이다. macOS(Apple Silicon)에는 정식 지원 휠이 없어
  이 머신에서 `pip/uv install vllm` 은 실패하거나 무의미하다(실행 불가).
- GPU 서버에서: `uv add vllm` (또는 별도 worker 이미지에 설치) 후 `vllm serve <model>` 로 OpenAI 호환
  API 서빙. `SERVING_STACK=vllm` (PRD §7.9) 으로 전환.

### 2.2 실 QLoRA 학습(torch/transformers/peft/trl + bitsandbytes)

- QLoRA 의 4bit 양자화(`bitsandbytes`)는 **CUDA 전용** — Apple Silicon/CPU 에서는 동작하지 않는다
  (MPS 백엔드 미지원). 따라서 실 QLoRA 학습은 NVIDIA GPU 환경(worker 이미지/노드)에서만 유효하다.
- **⚠️ 설치 전 필수 선행 조치 (중요 발견)**: `app/services/trainer.py::_real_available()` 는
  `peft`·`torch`·`transformers`·`trl` 4개 패키지의 **import 가능 여부만** 확인해 real/simulate 모드를
  자동 전환한다. 즉 이 4개를 설치하면 **환경 구분 없이(테스트 포함) 즉시 실학습 모드로 전환**된다.
  현재 133개 backend 테스트 전부가 simulate 모드(빠른 합성 학습)를 전제하므로, GPU 워커 이미지에
  이 패키지들을 설치하기 **전에** 다음 중 하나를 먼저 코드에 반영할 것을 강하게 권고한다:
  1. `Settings.force_training_mode: str = "auto"` (`auto`|`simulate`|`real`) 추가 —
     `_real_available()` 대신 이 플래그로 모드 결정. 기본값 `auto`(현재 동작 유지),
     테스트/CI 환경은 `FORCE_TRAINING_MODE=simulate` 로 고정.
  2. 또는 최소한 테스트 스위트의 모든 `client` 픽스처에 `monkeypatch.setattr(trainer, "_real_available", lambda: False)` 를 추가해 CI 안전성을 보장.
  - 이 조치 없이 GPU 이미지에 4개 패키지를 그대로 설치하면, 동일 코드베이스를 실행하는 CI/테스트
    환경에서도 (만약 같은 이미지를 쓴다면) 의도치 않게 실학습이 트리거될 수 있다.
- 선행 조치 반영 후 설치 예시(GPU 워커 이미지 Dockerfile 발췌):
  ```dockerfile
  RUN uv add torch transformers peft trl bitsandbytes accelerate datasets
  ENV FORCE_TRAINING_MODE=real
  ```
- 실행 시 `app/services/trainer.py::_train_real` 이 QLoRA SFT 를 실제로 수행(현재 코드는 plain LoRA
  로드 경로만 구현되어 있어, 4bit 양자화 로딩(`BitsAndBytesConfig`)을 실제로 적용하려면 `_train_real`
  에 `load_in_4bit=True` 로딩 설정을 추가하는 작업이 별도로 필요하다 — 현재는 QLoRA 설정값이
  `QLORA_DEFAULTS` 에 문서화만 되어 있고 `_train_real` 로딩부에는 아직 미적용 상태다).

### 2.3 llama.cpp GGUF 실 변환

- `pip install gguf` 만으로는 부족하다 — 모델 아키텍처별 텐서 매핑/양자화 로직은 llama.cpp 리포지토리의
  `convert_hf_to_gguf.py` 스크립트에 있다. GPU/빌드 환경에서:
  ```bash
  git clone https://github.com/ggml-org/llama.cpp
  cd llama.cpp && pip install -r requirements.txt
  python convert_hf_to_gguf.py <full_model_dir> --outfile out.gguf --outtype q4_k_m
  ```
- `GET /api/v1/tuning/jobs/{id}/export-plan?target=gguf` 가 생성하는 명령이 정확히 이 형태다
  (§7.14) — 지금은 명령 생성만, 이 문서의 절차로 별도 환경에서 실행.

## 3. 왜 이렇게 나눴나

- vLLM: macOS 에서 설치 자체가 무의미(미지원 플랫폼).
- 실 QLoRA: 하드웨어(CUDA) 문제 + **설치만으로 테스트 스위트 동작이 바뀌는 부작용**(2.2 항목) 발견 —
  선행 코드 변경 없이 설치하는 것은 위험하다고 판단해 이번 세션에서는 보류.
- llama.cpp: 설치 자체는 가능하나 리포지토리 클론+빌드가 필요해 "패키지 설치" 범위를 넘어서고,
  실제 변환 검증에는 실 모델 가중치가 필요해(§2.2 와 동일 제약) 이번엔 명령 생성까지만 유지.
- frontend 시험·MLX: 하드웨어 제약 없음(Apple Silicon 네이티브) + 설치만으로 부작용 없음(§2.2 같은
  자동 모드 전환 위험 없음) → 이번 세션에서 실제로 설치·구현·검증 완료.
