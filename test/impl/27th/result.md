# impl/27th 시험 결과 — 튜닝 모니터링 + 모델 export

- 일시: 2026-08-13
- 판정: **PASS** (pytest 92/92 — 신규 1, ruff clean, 빌드 OK, E2E 실기동)

| # | 케이스 | 결과 |
|---|---|---|
| 1 | 진행률 필드 | PASS — succeeded progress 100% / steps 4 |
| 2 | 실시간 폴링 | PASS — running 시 2초 주기 + 진행 바 |
| 3 | 이벤트 히스토리 | PASS — 히스토리 버튼 |
| 4 | export API | PASS — tar.gz 588B, 어댑터+manifest, 409/404 |
| 5 | UI 다운로드 | 코드 반영 |
| 6 | E2E | PASS — progress 100%, export tar.gz 다운로드·해제 확인 |

## 원인 (사용자 지적: 모니터링·export 누락)

running 잡 진행 표시 없음(이벤트만) + 결과물 다운로드 경로 부재.

## 구현 (wise-FP Stage7 progress_cb / Stage9 package 준용)

- **진행률**: `tuning_jobs` 에 progress_pct·current_step·total_steps 추가, 학습 스텝마다 `_set_progress` 갱신.
  잡 목록 API 에 노출. UI 는 running 잡 있으면 2초 폴링 + 진행 바(%·step).
- **히스토리**: `GET /jobs/{id}/events`(기존) → UI "히스토리" 버튼으로 시각+메시지 표시.
- **모델 export**: `GET /jobs/{id}/export` — succeeded 잡 어댑터 디렉토리를 tar.gz 스트리밍
  (StreamingResponse, Content-Disposition attachment). 미완료 409·미존재 404. UI "다운로드" 버튼.

## 수정·재시험 이력

1. test_tuning fixture — 잡 생성이 이제 백그라운드 워커 트리거 → 전역 SessionLocal/ADAPTER_ROOT 교체 추가.
   `test_job_lifecycle_and_plan` → `test_job_creation_and_plan`(complete 콜백은 test_trainer 가 커버).
2. **스키마 변경 → local.db 재생성 필요**: 신규 컬럼(progress_pct 등)이 기존 SQLite 테이블에 없어
   잡 생성 500. `create_all` 은 컬럼 추가 안 함 — dev local.db 삭제 후 재기동으로 해결(개발 DB).
   운영은 alembic migration(확장 지점).
