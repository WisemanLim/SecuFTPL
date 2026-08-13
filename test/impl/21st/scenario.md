# impl/21st 시험 시나리오 — 평가 게이트 지표 자동 입력

결함: 평가 기록 없이 게이트 판정 → `no evaluation result for v0.1.0` 실패 (2단계 수동 절차).
요구: 모델별 지표 자동 입력 → 수정 후 판정 또는 수정 없이 즉시 판정.

| # | 케이스 | 기대 |
|---|---|---|
| 1 | 템플릿 API | `GET /tuning/eval-template` — 승인 레코드 정답 JSON 에서 expected(severity·attack_ids/attack_mapping) 추출, prediction=expected 출발점, 비 JSON·needs_annotation 은 skipped 집계 |
| 2 | 원클릭 판정 | 자동 입력 행 그대로 evaluate → gate passed=true (E2E: `test_eval_template_from_approved_records`) |
| 3 | UI 자동 채움 | ⑥단계 진입 시 dataset_version 기준 자동 입력(무매칭 시 전체 승인분 fallback) |
| 4 | 원클릭 버튼 | "게이트 판정" = 지표 기록 → 판정 연속 수행, 통과 시 자동 다음. "평가 기록만" 분리 유지 |
| 5 | 회귀 | pytest + ruff + build 통과 |
