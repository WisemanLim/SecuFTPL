# impl/40th — 원스톱 파이프라인 스크립트 (사용자 요청)

인자: "모델 선택 → 데이터셋 수집(게이트·가명화·중복제거) → 검수 승인 → (증강) → 튜닝 잡 →
평가 게이트 → 리더보드 비교 → 배포 를 one-stop CLI 기반 shell script 로, 필요하면 make 로
backend 구동 포함 완료 후 종료도 포함."

PRD 에 없던 신규 스코프 — F8(파이프라인 CLI)을 "원스톱 오케스트레이션 스크립트"로 확장(§3 F8
행, §7.10)한 뒤 구현(step 4 준수).

## 범위

- `scripts/run-pipeline.sh`(신규) — bash + curl + jq 로 FastAPI HTTP API 를 순차 호출:
  0) 백엔드 헬스체크 → 미기동 시 `uv run uvicorn`(=`make dev` 동일 명령) 백그라운드 기동,
     완료 시 트랩(EXIT)으로 자동 종료(사전에 떠 있던 서버는 건드리지 않음)
  1) 모델 선택(`models/seed`+`models/{id}/pin`)
  2) 데이터셋 수집 — 합성 레코드 N건(기본 500, `DATASET_MIN_RECORDS` 게이트와 동일 기준) 일괄 ingest
  3) 검수 승인 — queued 전건 approve
  4) 증강(옵션, 기본 `keyword` — Ollama 불필요; `backtranslate`/`paraphrase` 는 Ollama 필요)
  5) 튜닝 잡 제출 + 상태 폴링(succeeded/failed)
  6) 평가 게이트(`batch/gate`)
  7) 리더보드 비교
  8) 게이트 통과 시 배포(어댑터 export, 미통과 시 차단)
  각 단계 응답을 `artifacts/pipeline-run-<timestamp>/` 에 저장.
- `Makefile` — `make pipeline` 타겟(스크립트 실행 alias).
- `.gitignore` — `artifacts/*` 추가.
- 백엔드/프런트 코드 변경 없음 — 기존 API 만 오케스트레이션.

## 시나리오

| # | 케이스 | 기대 결과 |
|---|---|---|
| 1 | 백엔드 미기동 상태에서 스크립트 실행 | 자동 기동 → 파이프라인 8단계 전부 성공 → 완료 시 자동 종료 |
| 2 | 백엔드가 이미 실행 중인 상태에서 실행 | 기존 서버 재사용, 완료 후에도 서버 유지(종료하지 않음) — 재확인: `curl /health` 여전히 200 |
| 3 | `RECORD_COUNT=20`(500건 미달) | 5단계에서 422(DATASET_MIN_RECORDS 게이트) → 스크립트 즉시 종료 + 백엔드 정리(트랩) |
| 4 | 기본 실행(500건, `아파치` 포함 합성 텍스트) | 4단계 키워드 증강 `augmented=500`(치환 대상 존재 확인) |
| 5 | `make pipeline` | 스크립트와 동일 결과 |
| 6 | 전체 backend 회귀 | 코드 변경 없음 — 기존 136건 그대로 통과 |

## 실행

수동 E2E(스크립트 자체가 시험 대상 — pytest unit 시험 대상 아님, README §8 실행방법 절차):
`./scripts/run-pipeline.sh` (기본 500건) / `RECORD_COUNT=20 ./scripts/run-pipeline.sh`(게이트 실패 케이스) /
서버 사전 기동 후 재실행(재사용 케이스) / `make pipeline`. 회귀 확인: `uv run pytest -q` + `uv run ruff check .`.
