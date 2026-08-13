# impl/23rd 시험 결과 — 위저드 순환 참조 크래시

- 일시: 2026-08-13
- 판정: **PASS** (빌드 OK)

## 원인

ReviewStep "승인 완료 → 다음" 버튼이 `onClick={onDone}` 으로 `advance` 를 직접 받아
**클릭 이벤트 객체가 `mark` 인자로 유입** → `statuses[current] = SyntheticEvent`
(nativeEvent→view→Window 순환 참조) → 22차에 추가된 sessionStorage 저장의
`JSON.stringify` 에서 크래시. (22차 이전에는 저장이 없어 잠복해 있던 결함.)

## 수정

1. 콜사이트: `onDone={advance}` 직접 전달 3곳(dataset·review·gate) → `() => advance()` 래핑.
2. 방어: `advance()` 내부에서 `mark === "skipped" ? "skipped" : "done"` 강제 —
   향후 이벤트 객체가 들어와도 statuses 는 항상 유효한 StepStatus 만 보유.
