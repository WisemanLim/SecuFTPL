# impl/43rd — 그룹 단위 일괄 승인/반려 (PRD §7.15, 2026-08-14)

인자: "그룹 단위 일괄 승인/반려 구현, 기존 개별 검수도 그대로 제공."

PRD 갱신(§7.15 그룹핑 UX 항목에 일괄 검수 추가 + 변경 이력) 후 구현(step 4 준수).

## 범위

- **backend** ([records.py](../../../app/api/records.py))
  - `POST /api/v1/records/queue/review-group` — `{dataset_version, action(approve|reject), reviewer}`:
    해당 그룹의 **pending 전건** 일괄 처리. 반려 시 증강본(lineage) 연쇄 폐기(개별 검수와 동일 규칙,
    그룹 밖 증강본 포함). pending 0건이면 404. 처리 목록·연쇄 반려 목록 반환.
  - 기존 개별 검수(`POST /{record_id}/review`)·삭제·조회 경로 변경 없음.
- **frontend** ([queue/page.tsx](../../../frontend/app/queue/page.tsx))
  - ① 그룹 테이블에 "일괄 액션" 컬럼(전체 승인/전체 반려, pending 상태에서만).
  - ② 세부 패널 헤더에도 동일 버튼. 실행 전 확인 팝업(반려는 연쇄 폐기 경고 포함).
  - 처리 후 그룹·세부·상세 동시 새로고침, 결과는 하단 로그에 표시.

## 시나리오

| # | 케이스 | 기대 결과 |
|---|---|---|
| 1 | 그룹 A(2건)+B(1건), A 일괄 승인 | A 2건 approved, B pending 유지, B 개별 승인도 정상(공존) |
| 2 | 승인 원본 → 증강 → 증강본 그룹 일괄 반려 | 증강본만 rejected, approved 원본 불변 |
| 3 | pending 없는 그룹 일괄 처리 | 404 |
| 4 | backend 회귀 | 기존 147건 + 신규 3건 = 150건 통과, ruff clean |
| 5 | frontend 회귀 | tsc --noEmit clean, Vitest 7건 통과 |

## 실행

- `uv run pytest` / `uv run ruff check app test`
- `cd frontend && npx tsc --noEmit && pnpm run test`
