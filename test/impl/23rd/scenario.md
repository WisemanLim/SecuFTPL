# impl/23rd 시험 시나리오 — 위저드 순환 참조 크래시

증상: `TypeError: Converting circular structure to JSON — Window` @ PipelinePage.useEffect
(sessionStorage 저장 stringify).

| # | 케이스 | 기대 |
|---|---|---|
| 1 | 원인 | `onClick={onDone}` → `advance(클릭 이벤트)` — SyntheticEvent(Window 순환)가 StepStatus 로 statuses 에 유입 |
| 2 | 콜사이트 정리 | `onDone={advance}`/`onClick={onDone}` 직접 전달 전부 `() => advance()` 래핑 (dataset·review·gate) |
| 3 | 방어 | `advance(mark)` — mark 가 "skipped" 아니면 무조건 "done" (이벤트 객체 유입 차단) |
| 4 | 빌드 | pnpm build 통과 |
