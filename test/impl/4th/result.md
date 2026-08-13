# impl/4th 시험 결과

- 일시: 2026-08-13
- 판정: **PASS** (pytest 41/41 — 신규 8 + 회귀 33, ruff 0 오류, 수정·재시험 0회)

| # | 케이스 | 결과 |
|---|---|---|
| 1~3 | 카탈로그·추론 | PASS |
| 4~6 | 시드·pin/manifest·download plan | PASS |
| 7~8 | 이벤트 스캔 유사판정 | PASS |
| 9 | 회귀+린트 | PASS |

## 설계 노트

- **네트워크 무의존 코어**: 실제 HF Hub polling(주 1회, `HF_POLLING_CRON`)은 ops 스케줄러가
  discovered 목록을 만들어 `POST /events/scan` 으로 주입 — 코어 로직은 오프라인 테스트 가능.
- **라이선스 추측 금지**: 카탈로그 license=None, 유사판정에서 미확인 기준은 제외(None 처리).
  gated 모델(meta-llama 등)은 pin/다운로드 전 모델카드 검토 필수(notes 유지).
- **다운로드 실행 없음**: download-plan 은 hf CLI 명령 문자열만 — 실행은 worker/사용자.
- manifest = pinned(revision 고정)만 — govtech N2SF 에어갭 반입 근거(COMPLIANCE 델타).
