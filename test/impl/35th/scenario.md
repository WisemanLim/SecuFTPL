# impl/35th — F9 실제 리소스 큐잉 (TOTAL_GPU_CAPACITY) + 배치 디스패치 결함 수정

근거: PRD `.docs/SecuFTPL-PRD.md` F9(§3), §7.12 "가드레일" 절. impl/29th 는 리소스 한도를
저장·조회만 했고(README "잔여: 리소스 상한 초과 시 실제 큐잉") 실제 동시성 게이트가 없었음.
feature-keyword 미지정 — README에 명시된 유일한 F9 잔여 항목을 이번 범위로 선정.

구현 중 발견한 연관 결함: `services/batch.py`의 `run_batch`가 pinned 모델별 튜닝 잡을
`create_job`으로 생성만 하고 어디에서도 `run_training_job`을 호출하지 않아, 배치가 만든 잡이
영원히 `queued`에 머무는 결함이 있었음(자동 야간 배치가 실제로는 학습을 전혀 진행 못함). 큐잉
디스패처를 도입하면서 배치도 같은 디스패처를 쓰도록 연결해 함께 해결.

## 범위

1. `app/core/config.py` — `total_gpu_capacity: int = 2` (`TOTAL_GPU_CAPACITY`).
2. `app/services/trainer.py` — `admit_or_queue(job_id)`(상한 내면 즉시 `run_training_job`, 초과
   시 queued 유지) · `dispatch_next_queued()`(잡 완료 시 오래 대기한 queued 잡을 FIFO로 재시도).
   `run_training_job` 종료 시 항상 `dispatch_next_queued()` 호출.
3. 호출부 교체: `api/tuning.py`(`post_job`·`retry_job`), `api/rag.py`(`upgrade`) —
   `run_training_job` 직접 백그라운드 등록 → `admit_or_queue`.
4. `services/batch.py`(`run_batch`) — 잡 생성 후 각 잡에 `admit_or_queue` 호출(이전엔 아무 디스패치도 없었음).

## 시나리오

| # | 케이스 | 기대 결과 |
|---|---|---|
| 1 | `total_gpu_capacity=1`, `max_gpu=2` 잡 제출 | 즉시 `queued` 유지(학습 시작 안 됨, progress_pct=0) |
| 2 | `total_gpu_capacity=2`, `max_gpu=1` 잡 제출 | 즉시 `succeeded`(상한 내 즉시 디스패치) |
| 3 | 상한 초과로 queued 인 잡 → 상한 상향 후 `/retry` | `succeeded`로 전환(재시도 시 재확인) |
| 4 | 배치가 pinned 모델로 잡 생성(`/batch/run`) | 생성된 잡이 `succeeded`로 전환(이전엔 queued 방치 결함) |
| 5 | 전체 회귀(`uv run pytest -q`) | 기존 121건 무변경 통과 |

## 실행

`uv run pytest -q test/test_resource_queue.py -v` + 전체 회귀 `uv run pytest -q` + `uv run ruff check .`
