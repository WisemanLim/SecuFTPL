# impl/28th 시험 결과 — 모델 상태·다운로드·다중 파이프라인·모델 상세

- 일시: 2026-08-13
- 판정: **PASS** (pytest 94/94 — 신규 2, ruff clean, 빌드 OK, E2E 실기동)

| # | 케이스 | 결과 |
|---|---|---|
| 1 | 다운로드 상태 전환 + 재다운로드 409 | PASS |
| 2 | 학습 제약(다운로드 필요) | PASS 422 |
| 3 | 모델 상세 API | PASS |
| 4 | UI 모델 상세·다운로드 폴링 | 코드 반영 |
| 5 | 파이프라인 downloaded/pinned 필터 | 코드 반영 |
| 6 | 새 파이프라인 리셋 | 코드 반영 |
| 7 | E2E | PASS — download→downloaded, usable True, 매니페스트 생성 |

## 원인 (사용자 지적)

- 모델 status 가 registered 뿐 → 다운로드 필요 여부 불명, 미다운로드 모델도 학습 시도 가능.
- 파이프라인이 단일 sessionStorage 상태 → 완료 후 새 파이프라인 구성 불가(①단계 대기 고착).

## 구현

- **모델 상태**: registered→downloading→downloaded. `POST /models/{id}/download`(백그라운드 시뮬,
  wise-FP download 준용) → 스냅샷 매니페스트 생성. `create_job` 이 downloaded/pinned 만 허용(그 외 422).
  UI: /models 행 클릭 → 상세 패널(다운로드/pin 버튼), downloading 2초 폴링, status 색상 구분.
- **모델 상세**: `GET /models/{id}/detail` — 메타·license·download_plan(hf CLI)·snapshot_manifest·
  usable_for_training. "다운로드 플랜" 상세 확인(사용자 추가 요구).
- **다중 파이프라인**: 위저드 헤더 "+ 새 파이프라인"(confirm→리셋) + ⑧배포 "새 파이프라인 시작".
  sessionStorage 초기화로 ①부터 재구성. ①모델 선택은 downloaded/pinned 만 노출(없으면 [모델] 안내).

## 수정·재시험

기존 잡 생성 테스트가 registered 모델 사용 → 이제 422. 헬퍼(_prepare·잡 생성 테스트)에 pin 추가로
downloaded 상당 상태 부여. test_registry fixture 도 다운로드 백그라운드 워커용 전역 SessionLocal 교체.
