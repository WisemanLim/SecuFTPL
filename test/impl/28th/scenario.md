# impl/28th 시험 시나리오 — 모델 상태·다운로드 + 다중 파이프라인 + 모델 상세

요구: ①모델 상태(registered/downloading/downloaded) + 다운로드된 모델만 학습 사용
②파이프라인 다중 세션(완료 후 새로 시작) ③모델 선택 시 상세(다운로드 플랜 등).

| # | 케이스 | 방법 | 기대 |
|---|---|---|---|
| 1 | 다운로드 상태 전환 | `POST /models/{id}/download` | downloading→downloaded(백그라운드), 매니페스트 생성, 재다운로드 409 |
| 2 | 학습 제약 | registered 모델로 잡 생성 | 422 (다운로드 필요) |
| 3 | 모델 상세 | `GET /models/{id}/detail` | 메타·상태·download_plan·snapshot·usable_for_training |
| 4 | UI 모델 상세 | /models 행 클릭 | 상세 패널 + 다운로드/pin 버튼, downloading 폴링 |
| 5 | 파이프라인 모델 선택 | 위저드 ① | downloaded/pinned 만 목록, 없으면 안내 |
| 6 | 새 파이프라인 | 헤더 "+ 새 파이프라인" / ⑧배포 | sessionStorage 리셋 → ①부터 재구성 |
| 7 | 회귀+E2E | pytest+ruff+build+실기동 | 전건 통과 |
