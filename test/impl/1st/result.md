# impl/1st 시험 결과

- 일시: 2026-08-12
- 판정: **PASS** (pytest 17/17, ruff 0 오류)

| # | 케이스 | 결과 |
|---|---|---|
| 1~5 | 정제 게이트 (스키마·비밀값·내부자산·주입·배치) | PASS (test_gate.py 8건) |
| 6~9 | 포맷 어댑터 (alpaca/sharegpt/openai-chat 왕복·교차·오류) | PASS (test_formats.py 4건) |
| 10~11 | API + 만족도 스키마 | PASS (test_api.py 5건) |
| 12 | ruff | PASS (0 오류, `.docs/` 제외 설정) |

## 수정·재시험 이력

1. `test_batch_report` FAIL — 테스트 픽스처가 모듈 레벨 META dict 를 공유,
   선행 테스트의 `del` 이 오염 → `dict(META)` 복사로 수정 → 재시험 PASS.
2. ruff 8 오류 → `.docs/` extend-exclude + `--fix` (Callable import, re.I→re.IGNORECASE, import 정렬) → 0 오류.

## 비고

- dpo-pairs·eval-set export 어댑터는 미구현(계획대로 E4·E5 연계 차기 이터레이션).
- 프로세스 매니저 기본값 honcho→pm2 변경(사용자 결정, Makefile·ecosystem.config.cjs 반영).
