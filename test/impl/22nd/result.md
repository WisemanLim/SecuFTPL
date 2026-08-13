# impl/22nd 시험 결과 — ⑥단계 지표 자동 채움 미동작

- 일시: 2026-08-13
- 판정: **PASS** (pytest 85/85, 빌드 OK — /pipeline 7.36kB)

## 원인 (실DB 재현)

`GET /tuning/eval-template` → `{"count":0,"skipped_unparsable":1,"rows":[]}` —
승인된 레코드가 문서 수집분(needs_annotation)뿐이라 자동 입력 행이 0건 → textarea 빈 상태.
부가로 새로고침 시 위저드 상태(useState) 소실, 화면은 갱신 전 번들이었음.

## 수정

1. **무매칭 fallback**: 파싱 가능한 정답 승인 레코드가 없으면 기본 샘플 행 자동 채움 +
   원인 안내("문서 레코드는 검수에서 정답 작성 후 반영").
2. **상태 영속**: 위저드 진행 상태(current/statuses/modelId/datasetVersion/jobId)를
   sessionStorage 저장·복원 — 새로고침/재진입에도 ⑥단계·모델 컨텍스트 유지.
3. **수동 채움 버튼**: "지표 자동 채우기" — 자동 실패/데이터 갱신 후 재시도용.
4. 스택 재기동으로 신규 번들 반영 (`make local-restart`).

## 재발 방지 안내

- 프론트 코드 변경 후 화면이 그대로면: `make local-restart` (pm2 재기동) + 브라우저 강력 새로고침.
