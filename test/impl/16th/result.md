# impl/16th 시험 결과 — 데이터셋 고도화

- 일시: 2026-08-13
- 판정: **PASS** (pytest 83/83 — 신규 10, ruff clean, 빌드 OK, E2E 문서 업로드→승인→추천)

| # | 케이스 | 결과 |
|---|---|---|
| 1~4 | 문서 수집·URL 정의 | PASS |
| 5~7 | 증강 추천·역번역·503 | PASS |
| 8 | E2E | PASS — `r-358a...` needs_annotation, 추천 `아파치→nginx/IIS` |
| 9 | UI 재배치 | PASS — 4단계 절차 + 채널 라디오 + webkitdirectory |
| 10 | 회귀 | PASS |

## 문서(Perplexity 조사) ↔ 구현 매핑

| 문서 근거 | 구현 |
|---|---|
| §수집·정규화 — "문서 OCR·품질검수", P0/P1/P2 소스 | PDF/DOCX/TXT/MD/HTML 텍스트 추출(pypdf·python-docx), trust_tier 채널 태깅 |
| §수집 원칙 — "정답이 명확함"이 규모보다 중요 | 문서는 **주석 대기(needs_annotation)** 레코드 — 정답은 검수 단계에서 분석가 작성 |
| §목표 분리 표 — task별 입력→출력 | 문서 수집 시 task_type 지시 프레임(TASK_PROMPTS) 적용 |
| §데이터 계약 — 출처·신뢰도 | source_uri/source_type/trust_tier 자동 태깅 |
| PRD §7.4 타언어 변환 | **역번역 ko→en→ko** — user 만 변형(assistant=라벨 불변), CVE/ATT&CK/CWE 자리표시 보호·복원, Ollama 백엔드(미기동 503) |
| PRD §7.4 키워드 치환 | **자동 추천** — 승인 레코드 빈도 키워드 × 보안 동의어 사전(SECURITY_SYNONYMS), 확정은 전문가 |

## 비고

- 사용자 디렉토리 = 브라우저 `webkitdirectory` 선택 → 멀티 업로드 경로 재사용
  (서버 경로 API/CLI 는 ops 용 유지). 브라우저는 로컬 경로 직접 접근 불가 — 표준 방식.
- PDF 는 텍스트 레이어 추출(pypdf) — 스캔 PDF OCR 은 확장 지점.
- 역번역 실동작은 Ollama + 모델 필요(`OLLAMA_BASE_URL`, 기본 qwen2.5:7b-instruct) — 코어는 fake translator 로 검증.
