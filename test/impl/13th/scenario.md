# impl/13th 시험 시나리오 — 데이터셋 수집 템플릿 자동 채움 (422 결함 대응)

결함: textarea 빈 상태로 수집 → 빈 배열 전송 → 422 `List should have at least 1 item`.
요구: task_type 종류 선택 시 messages JSONL 자동 채움 (근거 문서 데이터 수집 방법 반영).

| # | 케이스 | 방법 | 기대 |
|---|---|---|---|
| 1 | 템플릿 5종 | lib/templates.ts | alert_triage·cti_extraction·vuln_triage·policy_qa·safety_refusal — 문서 §권장 JSONL·안전 거부 예제 구조(근거·unknowns·citations·requires_human_approval) |
| 2 | 종류 선택 자동 채움 | select 변경 | autoFill 상태에서 즉시 교체, 사용자 수정 후엔 덮어쓰지 않음(+ 다시 채우기 버튼) |
| 3 | 빈 입력 가드 | 빈 textarea 수집 | API 미호출 — "수집할 레코드가 없습니다" 안내 (422 재발 방지) |
| 4 | 게이트 통과 | 템플릿 구조 레코드 ingest | queued=1, 내부 호스트명 가명화 |
| 5 | 빌드 | pnpm build | /pipeline·/datasets 컴파일 통과 |
| 6 | 회귀 | pytest + ruff | 65건 전건 통과 |
