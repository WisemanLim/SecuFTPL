# impl/42nd — 검수 큐 그룹핑 UX (PRD §7.15, 2026-08-14)

인자: "검수 목록 그룹핑 — 그룹(예: pipe-pipeline-20260813175850) 선택 시 세부 목록,
세부 선택 시 레코드 내용 3단계. 하단 로그 = 선택 그룹 요약."

PRD 갱신(§7.15 검수 큐 그룹핑 UX + 변경 이력) 후 구현(step 4 준수).
그룹 키 = `dataset_version`(레코드 ID 접두어와 동일 계열 — 수집 배치 단위).

## 범위

- **backend** ([records.py](../../../app/api/records.py))
  - `GET /api/v1/records/queue/groups?state=` — dataset_version 단위 그룹 요약:
    건수·grade 분포·task_type 분포·출처(source_uri) 집계·수집 시각 범위(first/last). 최근순 정렬.
  - `GET /api/v1/records/queue?state=&dataset_version=` — 그룹 선택 시 세부 목록 필터(미지정=전체, 기존 동작 유지).
- **frontend** ([queue/page.tsx](../../../frontend/app/queue/page.tsx)) — 3단계 재구성:
  ① 그룹 테이블(클릭=세부) ② 세부 목록(기존 테이블 + 승인/반려/삭제 + "그룹 목록으로")
  ③ 레코드 내용(기존 상세 패널). 하단 `out` 로그 = 선택 그룹 요약 JSON.
  승인/반려/삭제 후 그룹·세부 동시 새로고침(빈 그룹은 목록에서 소거).

## 시나리오

| # | 케이스 | 기대 결과 |
|---|---|---|
| 1 | 2개 dataset_version 수집 후 groups 조회 | group_count=2, 건수·grades·task_types·sources 집계, 시각 범위 존재 |
| 2 | queue?dataset_version=A | A 레코드만, 미지정 시 전체(기존 동작) |
| 3 | 빈 상태·state 전환 | pending 0그룹 → approve 후 state=approved 에 1그룹 |
| 4 | backend 회귀 | 기존 144건 + 신규 3건 = 147건 통과, ruff clean |
| 5 | frontend 회귀 | tsc --noEmit clean, Vitest 7건 통과 |

## 실행

- `uv run pytest` / `uv run ruff check app test`
- `cd frontend && npx tsc --noEmit && pnpm run test`
