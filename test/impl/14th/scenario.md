# impl/14th 시험 시나리오 — 검수 큐 상세 보기 + 시간 locale

요구: ①레코드 선택 시 내용 확인 ②created 등 시간 표기 locale 반영.

| # | 케이스 | 방법 | 기대 |
|---|---|---|---|
| 1 | 상세 API | `GET /api/v1/records/{id}` | payload(messages·metadata)+검수 상태 반환, 미존재 404 |
| 2 | 시간 직렬화 | queue/detail/jobs/runs `created_at` | UTC ISO8601(`+00:00`) — str() 나열 제거 |
| 3 | 큐 행 클릭 | /queue | 상세 패널: role별 messages·metadata·승인/반려/닫기 |
| 4 | 위저드 ③단계 | /pipeline 검수 행 클릭 | 인라인 내용 확인 |
| 5 | locale 변환 | `toLocale()` (lib/api.ts) | `new Date(iso).toLocaleString()` — 브라우저 locale |
| 6 | 빌드·E2E·회귀 | pnpm build + 프록시 detail 호출 + pytest | 전건 통과 |
