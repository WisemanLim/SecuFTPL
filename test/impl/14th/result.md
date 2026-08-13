# impl/14th 시험 결과 — 검수 큐 상세 보기 + 시간 locale

- 일시: 2026-08-13
- 판정: **PASS** (6/6 — pytest 66/66, ruff clean, 빌드 10라우트, E2E detail 응답)

| # | 케이스 | 결과 |
|---|---|---|
| 1 | 상세 API + 404 | PASS (`test_record_detail_and_iso_utc_time`) |
| 2 | UTC ISO 직렬화 | PASS — records·tuning jobs·batch runs 공통 `iso_utc()` |
| 3 | 큐 상세 패널 | PASS — 행 클릭 → messages/metadata/승인·반려, 액션 셀 클릭 전파 차단 |
| 4 | 위저드 인라인 확인 | PASS |
| 5 | locale 변환 | PASS — `toLocale()` 공용화(lib/api.ts), created 표기 전면 적용 |
| 6 | E2E | PASS — `created: 2026-08-13T02:11:27+00:00`, messages 3건 |

## 수정·재시험 이력

1. 첫 빌드 FAIL — page 파일에 `export const toLocale` (Next page 잉여 export) →
   `lib/api.ts` 로 이동 후 PASS.

## 시간 표기 원칙 (PRD 기록)

- **API**: naive DB 타임스탬프(UTC 저장)를 `+00:00` ISO8601 로 직렬화 — 서버 locale 무의존.
- **화면**: `toLocale()` = `new Date(iso).toLocaleString()` — 브라우저 locale/타임존 반영.
- 신규 시간 필드는 동일 규칙 필수 (`iso_utc` + `toLocale`).
