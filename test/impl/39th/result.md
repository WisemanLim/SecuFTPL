# impl/39th 시험 결과 — 증강: 패러프레이즈(LLM 문장 재구성)

- 일시: 2026-08-13
- 판정: **PASS**

| # | 케이스 | 결과 |
|---|---|---|
| 1 | 식별자 보존·lineage·quality_grade | PASS |
| 2 | 변화 없음 → 빈 목록 | PASS |
| 3 | `/records/augment`(paraphrase) Ollama 미기동 → 503 | PASS |
| 4 | 기존 backtranslate 503 테스트(문구 일반화 후) | PASS — 무변경 |
| 5 | `pnpm run build` + Vitest | PASS |
| 전체 | `uv run pytest -q` | PASS — 136 passed(기존 133건 + 신규 3건) |
| 린트 | `uv run ruff check .` | PASS |

## 생성/수정 파일

- `app/services/augment.py` — `paraphrase_record`·`paraphrase_records`·`ollama_paraphraser`
- `app/api/records.py` — `AugmentRequest.method` 에 `paraphrase` 추가, `/augment` 분기 통합
- `frontend/app/datasets/page.tsx` — "패러프레이즈 증강" 버튼
- `test/test_dataset_advanced.py` — 신규 3건(순수 로직 2건 + API 503 1건) + import 갱신

## 잔여

- PRD §7.4 증강 표 3항목(키워드 치환·역번역·패러프레이즈) 전부 구현 완료.
- GPU/Linux 전용 잔여 항목(vLLM, 실 QLoRA, llama.cpp 실 GGUF)은 `.docs/GPU-실학습-배포-가이드.md` 참조.
- 서빙 어댑터 실교체(ollama 연동), frontend 디자인 시스템(`/ui-design`) 미구현.
