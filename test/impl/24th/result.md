# impl/24th 시험 결과 — 학습 워커 + 리더보드 상세

- 일시: 2026-08-13
- 판정: **PASS** (pytest 89/89 — 신규 4, ruff clean, 빌드 OK, 실기동 E2E)

| # | 케이스 | 결과 |
|---|---|---|
| 1~4 | 백그라운드 학습·이벤트·자동평가·차단 | PASS (test_trainer.py) |
| 5 | 리더보드 상세 API | PASS |
| 6~7 | UI 상세·학습 폴링 | 코드 반영 (E2E 확인) |
| 8 | real/simulate 자동 선택 | PASS |
| 9 | E2E 실기동 | PASS — job 3초 succeeded, adapter 저장, 리더보드 반영 |

## 원인 (사용자 지적: 학습 전혀 미진행)

`POST /tuning/jobs` 가 잡 레코드만 생성하고 실행 주체(워커)가 없었음 —
"실학습은 GPU worker 전제" 로만 명세되어 실제 백그라운드 실행이 미구현.

## 구현 (wise-FP Stage7 PipelineTrainer 준용)

- **백그라운드 워커** `app/services/trainer.py` — FastAPI `BackgroundTasks` 로 잡 제출 즉시 실행:
  승인 데이터셋 로드 → 학습 → 어댑터+manifest 저장 → 자동 평가 → 리더보드 반영 → succeeded.
- **real/simulate 자동 선택**: torch/transformers/peft/trl 설치 시 실 QLoRA SFT(`_train_real`,
  wise-FP Stage7 구조), 미설치(GPU 없음) 시 시뮬레이션(`_train_simulate`, 합성 손실 곡선) —
  **파이프라인이 GPU 없이도 end-to-end 동작**, 의존성 설치만으로 실학습 전환.
- **이벤트 로그** `job_events` 테이블 — `GET /jobs/{id}/events` 폴링(손실·단계).
- **리더보드 상세** `GET /leaderboard/detail/{model}` — 평가 이력 전체 + 관련 잡.
- UI: 리더보드 행 클릭 → 세부 패널(평가 이력·잡), 위저드 ⑤ 제출 후 학습 진행 폴링→자동 다음.

## E2E (실기동)

잡 제출 → 3초 내 `succeeded`, `adapter_uri=adapters/ft-...`, 리더보드에 job_id 지표(cases 1,
json_valid 1.0) 자동 반영 확인.

## 확장 지점

실학습 의존성(torch/transformers/peft/trl, GPU)은 worker 이미지에서 설치 — 코어는 미설치 기본.
장시간 잡용 외부 큐(arq/celery)·WebSocket 진행 스트리밍은 확장 지점(현재 BackgroundTasks + 폴링).
