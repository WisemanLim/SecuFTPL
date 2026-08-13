# impl/35th 시험 결과 — F9 실제 리소스 큐잉 + 배치 디스패치 결함 수정

- 일시: 2026-08-13
- 판정: **PASS**

| # | 케이스 | 결과 |
|---|---|---|
| 1 | 상한 초과(`max_gpu=2` vs `total_gpu_capacity=1`) | PASS — `queued` 유지, progress_pct=0 |
| 2 | 상한 내(`max_gpu=1` vs `total_gpu_capacity=2`) | PASS — 즉시 `succeeded` |
| 3 | 상한 상향 후 `/retry` | PASS — `succeeded`로 전환 |
| 4 | 배치 생성 잡 디스패치 확인 | PASS — `succeeded`(이전 결함 수정 확인) |
| 전체 | `uv run pytest -q` | PASS — 125 passed(신규 4건 포함, 기존 121건 무변경) |
| 린트 | `uv run ruff check .` | PASS |

## 생성/수정 파일

- `app/core/config.py` — `total_gpu_capacity` 설정 추가
- `app/services/trainer.py` — `admit_or_queue`·`dispatch_next_queued` 신설, `run_training_job` 종료
  시 큐 재시도 연결
- `app/api/tuning.py` — `post_job`·`retry_job` 디스패치 경로를 `admit_or_queue`로 교체
- `app/api/rag.py` — `upgrade` 디스패치 경로를 `admit_or_queue`로 교체
- `app/services/batch.py` — `run_batch`에 잡 생성 후 `admit_or_queue` 호출 추가(디스패치 결함 수정)
- `.env.example` — `TOTAL_GPU_CAPACITY` 추가
- `test/test_resource_queue.py`(신규 4건), `test/test_feedback_batch.py`(배치가 이제 실제 학습을
  디스패치하므로 fixture에 core_db/ADAPTER_ROOT/sleep 패치 추가 — 다른 잡 관련 테스트 파일과
  동일 패턴)

## 설계 노트

- 디스패처는 FIFO 단일 후보만 확인(`dispatch_next_queued`) — 맨 앞 queued 잡이 여전히 상한을
  초과하면 뒤의 더 작은 잡을 건너뛰어 먼저 시작하지 않음(head-of-line blocking, 의도적 단순화).
  실사용에서 필요해지면 후보 목록 순회로 확장 가능.
- 시뮬레이션 학습은 동기 실행이라 진짜 동시성은 없음 — 상한은 "동시에 몇 개까지 running 상태를
  허용하는가"를 게이트하는 것으로, 실 GPU worker 도입 시 그대로 유효.

## 잔여

- frontend 자동화 시험(Vitest/Playwright) 미배선
- GGUF/MLX 실행, vLLM 양자화, ops cron 배선, 서빙 어댑터 실교체 등(README "다음 단계" 참조)
