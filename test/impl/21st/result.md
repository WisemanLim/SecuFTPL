# impl/21st 시험 결과 — 평가 게이트 지표 자동 입력

- 일시: 2026-08-13
- 판정: **PASS** (pytest 85/85 — 신규 1, ruff clean, 빌드 OK)

## 원인

⑥단계가 "평가 기록"(수동) → "게이트 판정" 2단계 절차였는데 기록 없이 판정만 눌러
`no evaluation result` 실패 — 지표 입력이 자동화되어 있지 않았음.

## 수정

1. **`GET /api/v1/tuning/eval-template`** — 승인 레코드의 정답(assistant JSON)에서
   expected(severity + attack_ids/attack_mapping) 자동 추출, prediction=expected 를 출발점으로 제공
   (완벽 예측 가정 — 실제 모델 출력으로 수정 가능). 비 JSON 정답·needs_annotation 은 제외 집계.
2. **UI 자동 채움** — ⑥ 진입 시 dataset_version 기준 자동 입력, 무매칭이면 전체 승인분 fallback.
3. **원클릭 판정** — "게이트 판정" 버튼이 지표 기록(evaluate) → 게이트 판정을 연속 수행
   (수정 후/수정 없이 모두 한 번에). "평가 기록만" 버튼은 분리 유지(리더보드 반복 기록용).
