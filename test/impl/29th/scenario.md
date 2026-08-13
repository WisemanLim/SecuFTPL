# impl/29th — F9 리소스/모니터링 세부설정 + 튜닝 시작 최소 데이터셋(500건) 게이트

근거: PRD `.docs/SecuFTPL-PRD.md` F9(§3), §7.5(튜닝 시작 게이트), §7.12(리소스/모니터링).

## 범위

1. 튜닝 잡 제출 시 승인(approved) 레코드가 `DATASET_MIN_RECORDS`(기본 500) 미만이면 422 차단.
2. 잡 제출 시 `max_gpu`/`max_vram_gb` 리소스 세부설정(옵션, 미지정 시 시스템 기본값 `JOB_MAX_GPU`/`JOB_MAX_VRAM_GB`).
3. `GET /api/v1/tuning/jobs/{id}/resources` — CPU/메모리(psutil 실측) + GPU util/VRAM
   (pynvml 있으면 실측, 없으면 시뮬레이션 라벨).

## 시나리오

| # | 케이스 | 기대 결과 |
|---|---|---|
| 1 | approved 3건으로 튜닝 잡 제출(기본 게이트 500 유지) | 422, 사유에 "500" 포함 |
| 2 | 잡 제출 시 `max_gpu=2, max_vram_gb=48` 지정 | 응답에 반영, 잡 row 저장 |
| 3 | `GET .../resources` 호출 | limits 일치, gpu_devices 길이=max_gpu, cpu/mem 0~100 범위 |
| 4 | 잡 제출 시 리소스 미지정 | `job_max_gpu`/`job_max_vram_gb` 설정 기본값 사용 |
| 5 | 기존 튜닝/배치/레지스트리 테스트(적은 승인건수) | `dataset_min_records=1`로 조정 후 기존 동작 그대로 통과 |

## 실행

`uv run pytest -q` (전체) + `uv run ruff check .`
