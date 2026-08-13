# impl/19th 시험 시나리오 — 상세 패널 액션 pill 정합 배치

요구: 액션(승인/반려/삭제/닫기)을 우측 정렬이 아닌 상태 pill **바로 옆**에 붙이고,
pending pill 과 동일한 글자·형태(크기·radius)로. 색상은 기존 유지.

| # | 케이스 | 기대 |
|---|---|---|
| 1 | 배치 | marginLeft:auto 제거 — 제목·pill·버튼 연속(gap 6) |
| 2 | 스타일 | `.btn-pill`: padding 1px 8px·radius 99px·11.5px — pill 과 동일 형태, 버튼 색상(그린/적색) 유지 |
| 3 | 빌드 | pnpm build 통과 |
