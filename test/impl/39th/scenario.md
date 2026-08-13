# impl/39th — 증강: 패러프레이즈(LLM 문장 재구성)

근거: PRD `.docs/SecuFTPL-PRD.md` §7.4 증강 표 — "패러프레이즈 | LLM 기반 문장 재구성" 행이
문서화만 있고 미구현 상태였음. README 잔여 항목 "증강 LLM 백엔드(번역·패러프레이즈)" 중
번역(역번역)은 이미 구현돼 있었고 패러프레이즈만 공백 — feature-keyword 미지정, 신규 설치
불필요(기존 역번역과 동일한 Ollama HTTP 호출 패턴 재사용)한 순수 코드 공백을 이번 범위로 선정.

## 범위

1. `app/services/augment.py` — `paraphrase_record`·`paraphrase_records`(순수 로직, 역번역과
   동일 규칙: user 메시지만 변형, CVE/ATT&CK/CWE 식별자 보호, 변화 없으면 None) +
   `ollama_paraphraser`(Ollama HTTP 백엔드).
2. `app/api/records.py` — `AugmentRequest.method` 패턴에 `paraphrase` 추가, `/augment` 엔드포인트
   분기 처리(기존 backtranslate 분기 통합, 503 에러 문구 "번역" → "LLM" 일반화).
3. `frontend/app/datasets/page.tsx` — "패러프레이즈 증강" 버튼 추가.

## 시나리오

| # | 케이스 | 기대 결과 |
|---|---|---|
| 1 | `paraphrase_records` — 식별자 포함 텍스트, fake paraphraser | 증강본 record_id=`<원본>-para-1`, lineage_of=원본, quality_grade=augmented, CVE/ATT&CK 식별자 보존, assistant 불변 |
| 2 | `paraphrase_records` — 변화 없는 텍스트(identity 함수) | 빈 목록(무의미 증강 배제) |
| 3 | `POST /records/augment`(method=paraphrase) — Ollama 미기동 | 503, "Ollama" 포함 |
| 4 | 기존 backtranslate 503 테스트 | 문구 변경 후에도 "Ollama" 포함 확인이라 무변경 통과 |
| 5 | `pnpm run build` + Vitest | 통과(datasets 페이지 버튼 추가만, 로직 변경 없음) |
| 6 | 전체 backend 회귀 | 기존 133건 무변경 + 신규 3건 통과 |

## 실행

`uv run pytest -q test/test_dataset_advanced.py -v` + 전체 회귀 `uv run pytest -q` +
`uv run ruff check .` + `cd frontend && pnpm run build && pnpm run test`.
