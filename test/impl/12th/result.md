# impl/12th 시험 결과 — E7 UI 개편

- 일시: 2026-08-13
- 판정: **PASS** (8/8 — 빌드·E2E·회귀, 수정·재시험 0회)

| # | 케이스 | 결과 |
|---|---|---|
| 1 | 브랜드 팔레트 | PASS — --acc #6fa01c(대비 확보)·--acc-bright #86bc25·틴트 #f6fae9, --sub 대비 4.5:1 보정 |
| 2 | 사이드바 | PASS — Shell.tsx (토글·localStorage·active·아이콘 모드) |
| 3~6 | 위저드·자동이동·복귀·스테퍼 | PASS — /pipeline 4.16kB 라우트 |
| 7 | 빌드·서빙 | PASS — 8 라우트, pipeline:200, "파이프라인 시작" CTA, local-all E2E |
| 8 | 백엔드 회귀 | PASS — pytest 65/65, ruff clean |

## 자동 이동 조건 (구현 기준)

| 단계 | 다음 이동 트리거 |
|---|---|
| ① 모델 선택 | 선택 확정 버튼 |
| ② 데이터셋 수집 | ingest 응답 `queued > 0` → 자동 |
| ③ 검수 승인 | approved ≥ 1 조건 버튼 활성 |
| ④ 증강 | 실행 성공 → 자동 / 건너뛰기(상태=skipped) |
| ⑤ 튜닝 잡 | 잡 생성 성공 → 자동 |
| ⑥ 평가 게이트 | `/batch/gate` passed → 자동 (평가 JSONL 직접 기록도 지원) |
| ⑦ 리더보드 | 비교 완료 버튼 |
| ⑧ 배포 | 완료 (실교체는 serving 확장 지점) |

이전 복귀: 완료/건너뜀 카드만 클릭 가능(navigable) — 복귀 시 현재 단계는 pending 으로.

## 비고

- 개별 페이지(모델·데이터셋·검수 큐·튜닝·리더보드)는 사이드바로 직접 접근 유지 —
  위저드는 순차 운용 표준 경로, 개별 페이지는 상세 작업(pin·포맷 변환·배치 이력)용.
- 스타일 근거: SeCuardian·Marketplace `front/src/index.css` @theme 그린 오버라이드 —
  SecuFTPL 은 Tailwind 미사용이라 동일 hex 를 CSS 변수로 이식.
