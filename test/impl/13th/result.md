# impl/13th 시험 결과 — 데이터셋 수집 템플릿 자동 채움

- 일시: 2026-08-13
- 판정: **PASS** (6/6)

| # | 케이스 | 결과 |
|---|---|---|
| 1 | 템플릿 5종 (lib/templates.ts) | PASS — task별 system/user/assistant + source_type 매핑 |
| 2 | 자동 채움/수정 보존 | PASS — autoFill 플래그, 수정 시 덮어쓰기 중단, "템플릿 다시 채우기" |
| 3 | 빈 입력 가드 | PASS — parse() 에서 차단, API 미호출 (422 재발 방지) |
| 4 | 게이트 통과 E2E | PASS — 템플릿 구조 ingest → queued=1, pseudonyms_added=1(호스트명) |
| 5 | 빌드 | PASS — /pipeline 6.4kB, /datasets 3.83kB |
| 6 | 회귀 | PASS — pytest 65/65, ruff clean |

## 템플릿 ↔ 문서 매핑 (근거: Perplexity-보안분야 LLM 모델 생성.md)

| task_type | source_type | 문서 근거 |
|---|---|---|
| alert_triage | internal_ir_report | §권장 JSONL 포맷 (FIN-WS-021 경보 예제 그대로) |
| cti_extraction | cti_report | §목표 분리 표 — CTI→ATT&CK/IOC 구조화 |
| vuln_triage | vuln_feed | §목표 분리 표 — CVE+KEV+자산 우선순위 |
| policy_qa | policy_doc | §목표 분리 표 — 인용 답변 (조건·citations) |
| safety_refusal | safety_seed | §안전 거부 예제 (refuse+safe_alternatives 그대로) |

공통 원칙(문서 §SFT 예제의 원칙 6요소): 현실적 입력·검색 근거·정답 판단·판단 근거·
불확실성(unknowns)·안전 경계(requires_human_approval) 전부 포함.

## 비고

- record_id 는 채움 시점 유니크(`r-<task>-<ts36>`) — 동일 내용 재수집은 content_hash 중복 스킵(정상).
- 위저드(②단계)·개별 데이터셋 페이지 양쪽 동일 적용.
- 템플릿 내부 자산 식별자(FIN-WS-021)는 수집 시 게이트 ⑤가 자동 가명화 — 의도된 데모.
