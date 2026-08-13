# impl/29th 시험 결과 — F9 리소스/모니터링 세부설정 + 튜닝 시작 500건 게이트

- 일시: 2026-08-13
- 판정: **PASS**

| # | 케이스 | 결과 |
|---|---|---|
| 1 | approved 3건 → 튜닝 잡 제출 (게이트 500 유지) | PASS — 422, "500" 포함 사유 반환 |
| 2 | `max_gpu=2, max_vram_gb=48` 지정 제출 | PASS — 응답·row 반영 |
| 3 | `GET /jobs/{id}/resources` | PASS — limits 일치, gpu_devices 길이 2, cpu/mem 0~100 |
| 4 | 리소스 미지정 시 설정 기본값(`job_max_gpu=1`, `job_max_vram_gb=24`) 적용 | PASS |
| 5 | 기존 튜닝/트레이너/레지스트리/배치 회귀(적은 승인건수, `dataset_min_records` 픽스처로 하향) | PASS |
| 전체 | `uv run pytest -q` | PASS — 97 passed |
| 린트 | `uv run ruff check .` | PASS — All checks passed |

## 수정/생성 파일

- `app/core/config.py` — `dataset_min_records`, `job_max_gpu`, `job_max_vram_gb` 설정 추가
- `app/models/tuning.py` — `TuningJobRow.max_gpu`/`max_vram_gb` 컬럼 추가
- `app/services/tuning.py` — `create_job` 최소 500건 게이트 + 리소스 파라미터
- `app/services/resources.py` (신규) — CPU/메모리(psutil)·GPU(pynvml 또는 시뮬레이션) 스냅샷
- `app/api/tuning.py` — `JobCreate`에 `max_gpu`/`max_vram_gb`, `GET /jobs/{id}/resources` 신설,
  `list_jobs`/`post_job` 응답에 리소스 필드 포함
- `pyproject.toml` — `psutil` 의존성 추가
- `.env.example` — `DATASET_MIN_RECORDS`/`JOB_MAX_GPU`/`JOB_MAX_VRAM_GB` 추가
- `test/test_resource_gate.py` (신규) — 게이트·리소스 시험 3건
- `test/test_tuning.py`·`test/test_trainer.py`·`test/test_registry.py`·`test/test_feedback_batch.py`
  — 기존 소량-승인 시나리오는 `dataset_min_records=1` 픽스처로 조정(회귀 방지)

## 잔여 (다음 이터레이션 후보)

- F9: 잡 큐잉(리소스 상한 초과 시 대기열) — 현재는 상한 값 저장·조회만, 동시성 강제는 미구현
- F10 RAG 추가학습·모델 업그레이드(§7.13)
- F11 다중 런타임(Ollama/vLLM/llama.cpp/MLX) 배포·풀모델 export(§7.14)
- F12 평가지표 가이드·추천
