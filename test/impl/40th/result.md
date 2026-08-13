# impl/40th 시험 결과 — 원스톱 파이프라인 스크립트

- 일시: 2026-08-13
- 판정: **PASS**

| # | 케이스 | 결과 |
|---|---|---|
| 1 | 백엔드 미기동 → 자동 기동 → 8단계 전부 성공 → 자동 종료 | PASS — 전체 소요 약 8초, `deploy-*.tar.gz` 산출 확인 |
| 2 | 백엔드 이미 실행 중 → 재사용, 종료 안 함 | PASS — 실행 후 `curl /health` 200 유지 확인 |
| 3 | `RECORD_COUNT=20`(게이트 미달) | PASS — 422 즉시 노출 후 종료, 트랩으로 백엔드 정리 확인 |
| 4 | 기본 500건, 키워드 증강 | PASS — `augmented=500`(콘텐츠에 "아파치" 포함하도록 수정 후 확인) |
| 5 | `make pipeline` | PASS — 스크립트 직접 실행과 동일 결과 |
| 6 | backend 전체 회귀 | PASS — 136 passed(무변경) |
| 린트 | `uv run ruff check .` | PASS |

## 생성/수정 파일

- `scripts/run-pipeline.sh`(신규) — 원스톱 파이프라인 오케스트레이션(curl+jq+bash)
- `Makefile` — `pipeline` 타겟 + `.PHONY` 등록
- `.gitignore` — `artifacts/*`
- `.docs/SecuFTPL-PRD.md` — F8(§3) 확장, §7.10 원스톱 스크립트 절 추가, 변경이력

## 설계 노트

- 스크립트는 신규 백엔드 API를 만들지 않고 **기존 엔드포인트만 오케스트레이션**한다 — 코드 회귀
  위험 없음(전체 136건 무변경 통과로 확인).
- 합성 데이터셋은 §7.2 canonical 스키마(cause 대응 답변 JSON: severity/attack_mapping/unknowns/
  citations)를 그대로 따르며, 정제 게이트·가명화·중복제거는 서버측 기존 `/records/ingest` 파이프라인이
  그대로 적용한다(스크립트가 우회하는 부분 없음).
- 평가 게이트는 기존 `_auto_eval_rows`(prediction=expected 자기 비교) 자동 평가 경로를 그대로
  타므로 항상 통과 — 이는 기존 eval-template 자동 입력 패턴과 동일한 기존 동작이며 스크립트가
  새로 추가한 우회가 아니다.
- 백엔드 lifecycle: 사전 실행 중이던 서버는 절대 건드리지 않음(트랩이 `STARTED_SERVER=1`일 때만 kill).

## 잔여

- 없음(요청 범위 완료). 필요 시 후속: 실 Ollama 연동 데모(`AUGMENT_METHOD=backtranslate|paraphrase`),
  다중 모델 비교 데모(여러 model_id 순회), CI 파이프라인에 스모크 테스트로 편입.
