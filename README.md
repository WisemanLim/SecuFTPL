# SecuFTPL

> 🇰🇷 한국어 | 🇺🇸 [English](README.en.md)

보안분야 LLM Fine-Tune Pipeline 플랫폼 — 보안 데이터셋 구축(수집·정제·증강) → 다중 베이스모델
파인튜닝 → 평가 비교 → Agent 피드백 루프 → 야간 배치 자동 재튜닝·재배포.

> **스캐폴딩**: `wise-dev-standard` / 프로파일 `python-fastapi` / 도메인 `ict-saas` (+govtech·finance 델타)
> **문서**: [PRD](.docs/SecuFTPL-PRD.md) · [COMPLIANCE.md](COMPLIANCE.md) · [시험 표준](test/README.md)

## 아키텍처 / 디렉터리

```
app/
├── main.py               # FastAPI 엔트리포인트 (lifespan: DB init, /supervisor UI)
├── cli.py                # secuftpl CLI — frontend 없이 파이프라인 실행 (F8)
├── web/
│   └── supervisor.html   # Supervisor 파이프라인 시험 UI (F7, 로그인 없음·내부망 전용)
├── core/
│   ├── config.py         # pydantic-settings (.env 주도)
│   ├── db.py             # SQLAlchemy 엔진·세션 (DATABASE_URL)
│   └── schemas.py        # canonical sft-messages 스키마 (PRD §7.2)
├── models/
│   ├── records.py        # dataset_records(검수 큐)·pseudonym_map(가명화 매핑)
│   └── registry.py       # model_registry (베이스모델 레지스트리, F2)
├── services/
│   ├── gate.py           # 정제 게이트: 비밀값/내부자산/프롬프트주입 탐지 (§7.3 ②④⑦)
│   ├── sanitize.py       # 가명화: 안정 토큰 치환 <KIND_0001> (§7.3 ⑤)
│   ├── dedup.py          # 완전(sha256)·근접(shingle Jaccard) 중복 제거 (§7.3 ⑥)
│   ├── formats.py        # F6 어댑터: alpaca/sharegpt/openai-chat ↔ canonical + dpo-pairs/eval-set export
│   ├── catalog.py        # 시드 카탈로그 pilot 12/core/all (다운로드 스크립트 준용)
│   ├── hf_registry.py    # 시드·유사판정·manifest·download plan (§7.5)
│   ├── model_download.py # 모델 다운로드 워커: registered→downloading→downloaded (F2)
│   ├── augment.py        # E4 증강: 키워드 치환(보호 식별자 거부)·lineage (§7.4)
│   ├── evaluate.py       # E3 평가 러너: json_valid/severity/attack F1 (§5)
│   ├── tuning.py         # E3 잡 오케스트레이션·QLoRA 플랜·리더보드
│   ├── trainer.py        # 학습 워커: 백그라운드 QLoRA(real/simulate 자동)·자동 평가 (§7.5)
│   └── batch.py          # E6 야간 배치: 트리거 3모드·평가 게이트·이력 (§7.9)
└── api/
    ├── datasets.py       # /api/v1/datasets — validate·convert·formats
    ├── records.py        # /api/v1/records — ingest·augment·queue·review
    ├── registry.py       # /api/v1/models — seed·pin·manifest·events/scan·download-plan
    ├── tuning.py         # /api/v1/tuning — jobs·plan·complete·evaluate·leaderboard·resources(F9)·export-plan(F11)·eval-guide(F12)
    ├── feedback.py       # /api/v1/feedback — Agent 환류(만족도)·stats (E5)
    ├── batch.py          # /api/v1/batch — should-run·run·gate·runs·cron-plan (E6)
    └── rag.py            # /api/v1/rag — synthesize·upload·upgrade (F10)
frontend/                 # E7 독립 Next.js 앱 (wise-FP 참고만 — 로그인 없음)
├── app/                  # 대시보드·pipeline(단계별 위저드)·models·datasets·queue·tuning(리소스·export F9/F11)·leaderboard(평가가이드 F12)·rag(코퍼스 합성·모델 업그레이드 F10)
├── components/           # Shell(좌측 접이식 사이드바)·Stepper(단계 상태 카드)
├── lib/api.ts            # same-origin /api/* (rewrites 프록시 → FastAPI)
└── next.config.mjs       # NEXT_PUBLIC_API_BASE 프록시 설정
# 스타일: Genians CI 그린(#86BC25) — SeCuardian front 준용 (PRD §7.11)
test/                     # pytest + 시험표준 (dev-env/, impl/<Nth>/)
scripts/                 # run-pipeline.sh — 원스톱 파이프라인 오케스트레이션(F8 확장)
.docs/                    # PRD·참고 문서·모델 다운로드 스크립트
```

## 기술 스택

Python 3.12+ · FastAPI · uv · SQLAlchemy 2/Alembic · PostgreSQL 17 · Redis 7.4 ·
Docker Compose v2 · Helm(K8s) · GitHub Actions(uv sync→ruff→pytest)

## 사전 요구사항

- Python 3.12+, [uv](https://docs.astral.sh/uv/), Docker Desktop(Compose v2), GNU Make
- Node.js (기본 프로세스 매니저 pm2 를 `npx` 로 실행 — 대안: `PROC_MGR=honcho`)
- (선택) `uv sync --extra mlx` — F11 실 MLX export(Apple Silicon 전용, `mlx-lm`)
- (선택) frontend e2e 시험: `cd frontend && pnpm exec playwright install chromium`(Vitest 는 `pnpm install` 만으로 충분 — devDependencies 에 이미 포함)
- 점검: `make preflight`

## 환경 설정 (.env 매트릭스)

| 파일 | DB | 용도 |
|---|---|---|
| `.env.local` | sqlite (`sqlite:///./local.db`) | 직접 실행, 외부 의존 최소 |
| `.env.dev` | postgres (compose) | 공유 개발 |
| `.env.staging` | postgres | prod 동등 리허설 |
| `.env.prod` | 키 목록만 | Vault/Secret Manager 주입 전제 |

운영 옵션(PRD §7.9): `FT_TRIGGER_MODE=schedule` · `HF_EVENT_MODE=polling`(주 1회) ·
`SATISFACTION_SCALE=binary` · `SERVING_STACK=ollama` · `DATASET_MIN_RECORDS=500`(튜닝 시작 게이트) ·
`JOB_MAX_GPU=1`/`JOB_MAX_VRAM_GB=24`(잡 리소스 기본값, F9) ·
`TOTAL_GPU_CAPACITY=2`(시스템 전체 동시 학습 상한, 초과 시 큐잉) ·
`DOC_PARSER=auto`(PDF 파싱 백엔드: auto|pypdf|docling, F20). 전체 키는 [.env.example](.env.example).
**실 시크릿 커밋 금지** — `.gitignore` 가 `.env.*` 차단(`!.env.example`).

## 실행 방법

```bash
uv sync && make front-install    # 의존성 설치 (백엔드 + frontend)
make local-all                   # ★ 표준 경로: infra + web(api) + front 일괄 기동 (pm2)
make ps / local-logs / local-stop
make dev-all / dev-build         # dev 전체 스택 컨테이너 (api + front + infra, .env.dev)
# 디버깅용 단일 실행:
make dev                         # api 만 포그라운드 (uvicorn --reload)
make front-dev                   # front 만 (Next dev)
make up ENV=dev                  # infra 만 (postgres+redis)
```

`local-all` 은 ecosystem.config.cjs(pm2 기본) 또는 Procfile.dev(`PROC_MGR=honcho`)로
**web+front 를 함께** 관리한다 — 포트·API 주소는 `.env.<env>` 의 `API_PORT`/`FRONT_PORT`/`BIND_HOST` 참조.

## 접속 / 포트

**포트 SSOT (PRD §7.9)**: 모든 리스닝 포트·바인드 IP는 `.env.<env>` 가 단일 출처.
Makefile 이 honcho 엔 `-e .env.$(ENV)`, pm2 엔 `ENV_FILE=.env.$(ENV)` 로 주입 —
충돌 시 `.env.local` 의 `API_PORT` 만 바꾸면 전 구성(compose·Procfile·pm2)에 반영된다.

| 서비스 | 포트 (기본) | 비고 |
|---|---|---|
| API | `127.0.0.1:8000` | `API_PORT`, Swagger: `/docs`, **Supervisor UI: `/supervisor`** |
| Frontend (E7) | `127.0.0.1:3000` | `FRONT_PORT`, `/api/*` 는 rewrites 프록시. **`/pipeline` = 단계별 위저드**(자동 다음 이동·이전 복귀). local-all 포함, compose `front`(dev+) |
| PostgreSQL | `127.0.0.1:5432` | `POSTGRES_PORT` (compose) |
| Redis | `127.0.0.1:6379` | `REDIS_PORT` (compose) |
| Ollama(스텁) | `127.0.0.1:11434` | compose 주석 해제 시 |

## API

| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/health` | 헬스 체크 |
| GET | `/api/v1/datasets/formats` | 지원 포맷 목록 (canonical=sft-messages) |
| POST | `/api/v1/datasets/validate` | canonical 레코드 배치 검증(정제 게이트 리포트) |
| POST | `/api/v1/datasets/convert` | 포맷 변환 (alpaca/sharegpt/openai-chat ↔ canonical, export: dpo-pairs·eval-set) |
| GET | `/api/v1/datasets/export` | **데이터셋 다운로드**(F13) — `format`/`review_state`(기본 approved)/`dataset_version` 필터, JSONL 스트림. `with_manifest=true` 면 zip(dataset+manifest — 출처 집계·sha256) |
| GET | `/api/v1/datasets/export/manifest` | manifest 미리보기 — 건수·분포·**출처별 집계(source_uri·license + DPI: creator/license_url/provenance_notes)**·파일 sha256 (전문가 검증용) |
| GET | `/api/v1/datasets/export/lmeval-task` | **lm-evaluation-harness 태스크 YAML**(F16) — eval-set export 와 짝으로 표준 하네스 등록 |
| GET | `/api/v1/datasets/decontam?train_version=&eval_version=&k=13` | **13-gram 디컨탬**(F18) — 학습 후보 vs 평가셋 오염 검사(검사만, 삭제 없음) |
| GET | `/api/v1/datasets/runs` · `/runs/{run_id}` | **수집·정제 run 이력/상세**(F15) — 단계별 통과/차단 건수·사유 샘플·출처 집계, 채널 필터 |
| POST | `/api/v1/records/ingest` | 수집: **게이트③ 출처 확인(F14 — `source_uri`·`source_hash_sha256` 누락 시 `rejected_attribution`)**→가명화→중복제거→pending 적재, 응답에 `run_id` 포함 |
| POST | `/api/v1/records/upload` | **파일(멀티) 업로드** — JSONL/JSON(F6 변환) + **문서 PDF/DOCX/TXT/MD/HTML**(텍스트 추출→주석 대기 레코드). UI 디렉토리 선택도 이 경로 |
| POST | `/api/v1/records/collect/dir` | 서버 경로 glob 수집 (CLI/ops 용) |
| POST | `/api/v1/records/collect/url` | **인터넷 수집** — 화이트리스트+SSRF 차단, 응답 유형 자동 판별(JSON=레코드/HTML=문서), T3_untrusted |
| GET | `/api/v1/records/augment/suggestions` | **치환 후보 자동 추천** — 승인 레코드 빈도×보안 동의어 사전 |
| GET | `/api/v1/records/queue/groups?state=` | **검수 큐 그룹 요약** — dataset_version 단위 건수·grade/task_type 분포·출처 집계·수집 시각 범위 (UI ①그룹 단계) |
| POST | `/api/v1/records/queue/review-group` | **그룹 일괄 승인/반려** — `{dataset_version, action, reviewer}`, pending 전건 처리·반려 시 lineage 연쇄 폐기 (개별 검수 공존) |
| GET | `/api/v1/records/queue?state=pending&dataset_version=` | 검수 큐 조회 — `dataset_version` 필터(그룹 선택 시 세부 목록), **출처(source_uri·license) 상시 노출(F14)**, created_at=UTC ISO(화면 locale 변환) |
| GET | `/api/v1/records/{record_id}` | 레코드 상세 (payload 내용 확인 — 검수용) |
| DELETE | `/api/v1/records/{record_id}` | 레코드 삭제 — 증강본 연쇄 삭제, UI 는 확인 팝업 후 호출 |
| POST | `/api/v1/records/{record_id}/review` | 승인/반려 (`{"action":"approve\|reject","reviewer":"..."}`) — 반려 시 증강본 연쇄 폐기 |
| POST | `/api/v1/models/seed` | 카탈로그 시드 (`{"profile":"pilot\|core\|all"}`, 멱등) |
| GET | `/api/v1/models?status=&tier=` | 레지스트리 목록 (status: registered/downloading/downloaded/pinned…) |
| GET | `/api/v1/models/{model_id}/detail` | **모델 상세** — 메타·상태·다운로드 플랜·스냅샷 매니페스트 |
| POST | `/api/v1/models/{model_id}/download` | **모델 다운로드**(백그라운드) — downloaded 만 학습 사용 가능 |
| POST | `/api/v1/models/{model_id}/pin` | revision 고정 (`{"revision":"<hash>"}`) — 에어갭 반입 근거 |
| GET | `/api/v1/models/manifest` | pinned 모델 manifest |
| POST | `/api/v1/models/events/scan` | 신규 모델 이벤트 주입 → 유사판정 → candidate (ops 스케줄러가 `HF_POLLING_CRON` 주기 호출) |
| GET | `/api/v1/models/{model_id}/download-plan` | hf CLI 다운로드 명령 생성 (실행 없음) |
| POST | `/api/v1/records/augment` | 승인 원본 증강 → 큐 재편입 — `method: keyword`(치환 사전) \| `backtranslate`(ko→en→ko) \| `paraphrase`(LLM 문장 재구성) — 뒤 둘은 Ollama 필요·미기동 503 |
| POST | `/api/v1/tuning/jobs` · GET `/jobs` | 튜닝 잡 생성(승인 레코드 **500건 미만이면 422**, `max_gpu`/`max_vram_gb` 옵션 — 시스템 전체 상한(`TOTAL_GPU_CAPACITY`) 초과 시 즉시 시작 대신 **queued 유지**)·목록 |
| GET | `/api/v1/tuning/jobs/{id}/resources` | **리소스 모니터링**(F9) — CPU/메모리(실측) + GPU util/VRAM(pynvml 실측 또는 시뮬레이션) |
| GET | `/api/v1/tuning/jobs/{id}/events` | 학습 진행 이벤트(손실·단계) 폴링 = 히스토리 |
| WS | `/api/v1/tuning/jobs/{id}/stream` | **실시간 스트리밍**(F9) — 상태/진행률/신규 이벤트 push(0.3초 주기), succeeded/failed 도달 시 최종 스냅샷 후 종료. 폴링(`/events`) 대안 |
| GET | `/api/v1/tuning/jobs/{id}/export` | **모델 다운로드** — `format=adapter`(기본, tar.gz) \| `full`(어댑터 merge 풀모델, F11) |
| GET | `/api/v1/tuning/jobs/{id}/export-plan` | **런타임 변환 플랜**(F11) — `target=gguf`(Ollama/llama.cpp) \| `mlx`(Apple Silicon), 명령 생성만·실행 없음 |
| POST | `/api/v1/tuning/jobs/{id}/export/mlx` | **MLX 실 변환 실행**(F11) — `mlx-lm` 설치 시(`uv sync --extra mlx`) 실제 변환, 미설치 501·풀모델이 실 HF 가중치가 아니면 422 |
| POST | `/api/v1/tuning/jobs/{id}/retry` | queued/failed 잡 재실행(백그라운드 재투입) |
| DELETE | `/api/v1/tuning/jobs/{id}` | 잡 삭제(이벤트 로그 연쇄, running 차단) |
| GET | `/api/v1/tuning/jobs/{id}/plan?lora_variant=` | QLoRA 학습 플랜(YAML) 생성 — `lora_variant=lora\|rslora\|dora`(F19) |
| GET | `/api/v1/tuning/jobs/{id}/train-plan/mlx` | **mlx-lm LoRA 실학습 명령 플랜**(F19, Apple Silicon) — 생성만, 실행은 worker/수동 |
| POST | `/api/v1/tuning/jobs/{id}/complete` | 외부 worker 콜백 (지표 → 리더보드) |
| GET | `/api/v1/tuning/leaderboard/detail/{model_id}` | **모델 세부내용** — 평가 이력(eval_id) + 튜닝 잡 |
| DELETE | `/api/v1/tuning/leaderboard/{eval_id}` | 평가 결과 1건 삭제(잡·모델 유지) |
| GET | `/api/v1/tuning/eval-guide` | **평가지표 가이드·추천**(F12) — `task_type`·`case_count` 기반 추천 지표 세트 + 가이드 문구 |
| GET | `/api/v1/tuning/eval-template` | 승인 레코드 정답에서 평가 지표 행 자동 생성 (⑥단계 자동 입력) |
| POST | `/api/v1/tuning/evaluate` | 예측 배치 평가 → 리더보드 반영 |
| GET | `/api/v1/tuning/leaderboard` | 모델 간 비교 (attack_f1 기본 정렬) |
| POST | `/api/v1/feedback` · GET `/feedback/stats` | Agent 질의/답변+만족도 환류·집계 (E5) |
| GET | `/api/v1/batch/should-run` · POST `/run` | 배치 트리거 판정·실행 (E6, ops cron 호출) |
| POST | `/api/v1/batch/gate` · GET `/runs` | 배포 게이트(하한+회귀 검사)·이력 |
| GET | `/api/v1/batch/cron-plan` | **ops cron 배선** — 야간 배치·HF polling crontab 라인 생성(실행/설치 없음, `crontab -e` 로 직접 반영) |
| POST | `/api/v1/rag/synthesize` · `/upload` | **RAG 코퍼스 → 합성 QA 레코드**(F10) — 텍스트/문서(PDF·DOCX·TXT·MD·HTML) 청킹 → cause/resolution 합성 → 검수 큐 편입. `diversify=true`(F21): 질문 유형 회전+키워드 명시 커버리지 합성, 응답에 coverage 리포트 |
| POST | `/api/v1/rag/upgrade` | **모델 업그레이드**(F10) — 승인된 (RAG 합성 포함) 데이터셋으로 continual fine-tuning 잡 제출, `continual_from_job_id`(선택)로 이어학습 기준 지정 |

```bash
curl -s localhost:8000/api/v1/datasets/convert -H 'content-type: application/json' -d '{
  "items": [{"instruction": "경보 분석", "output": "결과"}],
  "source": "alpaca", "target": "canonical",
  "meta_defaults": {"record_id": "r-1", "dataset_version": "v0.1.0"}
}'
# → {"count":1,"items":[{"messages":[...],"metadata":{...}}]}

curl -s localhost:8000/api/v1/rag/synthesize -H 'content-type: application/json' -d '{
  "documents": [{"title": "threat-report-1", "text": "위협 리포트 본문..."}],
  "task_type": "cti_extraction", "dataset_version": "v0.2.0"
}'
# → {"documents":1,"chunks":N,"ingest":{"queued":N,...}}  — 승인 후 /rag/upgrade 로 학습

curl -s localhost:8000/api/v1/tuning/jobs/ft-xxxx/export-plan?target=gguf
# → {"job_id":"ft-xxxx","target":"gguf","command":"python convert_hf_to_gguf.py ..."}
```

## Supervisor UI · CLI (F7·F8)

- **UI**: `make dev` 후 `http://127.0.0.1:8000/supervisor` — ①모델 선택(시드/pin/플랜)
  ②사용용도(task_type) ③데이터셋 JSONL 검증·수집·변환 ④검수 큐 승인/반려 ⑤튜닝 실행(E3 예정).
  로그인 없음 — **내부망 전용**, 외부 노출 시 인증 게이트웨이 필수.
- **CLI**: frontend 부재 환경 — API 서버 없이 DB 직접 실행.

```bash
uv run secuftpl dataset validate data.jsonl        # invalid 시 exit 1 (배치 게이트)
uv run secuftpl dataset convert in.jsonl --source alpaca --target canonical --out out.jsonl
uv run secuftpl dataset ingest data.jsonl && uv run secuftpl dataset queue
uv run secuftpl dataset collect-dir ./corpus --pattern '*.jsonl'   # 디렉토리 수집
uv run secuftpl dataset collect-url https://raw.githubusercontent.com/...jsonl  # 화이트리스트 URL
uv run secuftpl dataset review r-0001 --action approve --reviewer soc_01
uv run secuftpl models seed --profile pilot
uv run secuftpl models pin Qwen/Qwen3-14B --revision <hash>
uv run secuftpl models manifest
uv run secuftpl models scan discovered.jsonl       # 이벤트 유사판정 → candidate
uv run secuftpl models download-plan Qwen/Qwen3-14B
uv run secuftpl dataset augment --substitutions '{"아파치":"nginx"}'
uv run secuftpl dataset export out.jsonl --format alpaca      # F13 다운로드 + manifest(.manifest.json)
uv run secuftpl dataset export out.jsonl --input other.jsonl  # DB 대신 별도 파일 입력(오프라인 재가공)
uv run secuftpl dataset runs                                  # F15 수집·정제 run 이력 (--run-id 상세)
uv run secuftpl dataset backfill-attribution                  # F14 출처 누락 레거시 감지(dry-run, --apply 반영)
uv run secuftpl tune create Qwen/Qwen3-14B --dataset-version v0.1.0
uv run secuftpl tune plan <job_id>                 # QLoRA 플랜 → worker 실행
uv run secuftpl tune evaluate preds.jsonl --model-id m --dataset-version v1
uv run secuftpl tune leaderboard
uv run secuftpl batch run                          # 야간 배치 (ops cron 진입점)
uv run secuftpl batch gate <model_id> --dataset-version v1   # 미통과 시 exit 1
```

## 원스톱 파이프라인 스크립트 (F8 확장)

`scripts/run-pipeline.sh` — 모델 선택 → 데이터셋 수집(게이트·가명화·중복제거) → 검수 승인 →
(증강) → 튜닝 잡 → 평가 게이트 → 리더보드 비교 → 배포(export) 를 HTTP API 로 한 번에 실행.
백엔드 미기동 시 `make dev` 와 동일한 명령으로 자동 기동, 완료 시 자동 종료(이미 떠 있던 서버는
건드리지 않음).

```bash
make pipeline                          # 또는: ./scripts/run-pipeline.sh
RECORD_COUNT=1000 MODEL_ID=Qwen/Qwen3-32B ./scripts/run-pipeline.sh   # 옵션 오버라이드
AUGMENT_METHOD=backtranslate ./scripts/run-pipeline.sh                # Ollama 필요
```

주요 환경변수: `MODEL_ID`(기본 `Qwen/Qwen3-14B`) · `DATASET_VERSION`(기본 자동 타임스탬프) ·
`RECORD_COUNT`(기본 500, `DATASET_MIN_RECORDS` 게이트와 동일 — 미달 시 튜닝 단계 422) ·
`AUGMENT`/`AUGMENT_METHOD`(기본 `true`/`keyword`, 오프라인) · `EXPORT_FORMAT`(기본 `adapter`) ·
`API_PORT`(기본 8000). 각 단계 응답은 `artifacts/pipeline-run-<timestamp>/` 에 JSON/tar.gz 로 저장.
필수 도구: `curl`·`jq`·`uv`·`python3`(합성 레코드 생성, stdlib만 사용).

## 테스트

```bash
make test          # uv run pytest (test/ 단일 트리, backend 169건)
make front-test    # frontend Vitest 단위 시험 (7건)
make front-test-e2e  # frontend Playwright e2e (2건, dev 서버 자동 기동)
```

차수별 기록: `test/dev-env/`(환경 검증) · `test/impl/1st/`(E1 1차) · `2nd/`(포트 SSOT) ·
`3rd/`(가명화·중복제거·검수 큐·DPO/eval export) · `4th/`(모델 레지스트리) · `5th/`(Supervisor UI·CLI) ·
`6th/`(튜닝·평가·리더보드) · `7th/`(증강) · `8th/`(Agent 환류) · `9th/`(야간 배치) ·
`10th/`(독립 frontend 빌드·프록시 E2E) · `11th/`(구동 통합 — local-all=web+front, compose front) ·
`12th/`(UI 개편 — 그린 브랜드·사이드바·파이프라인 위저드) · `13th/`(task별 JSONL 템플릿 자동 채움·빈 입력 가드) ·
`14th/`(검수 큐 상세 보기·시간 locale 표기) · `15th/`(수집 채널 — 파일 멀티·디렉토리·URL, wise-FP A/B/C) ·
`16th/`(데이터셋 고도화 — 문서 수집·사용자 디렉토리·URL 수집 정의·증강 추천/역번역) ·
`17th/`(검수 큐 삭제 — lineage 연쇄·확인 팝업) · `18th~19th/`(상세 패널 액션 배치) ·
`20th/`(수집 자동 이동 판정) · `21st/`(평가 게이트 지표 자동 입력) · `22nd~23rd/`(위저드 상태 영속·순환참조) ·
`24th/`(학습 워커 백그라운드 QLoRA·리더보드 상세) · `25th/`(잡 후속처리 — 재실행·삭제) · `26th/`(리더보드 상세 잡 액션·평가 결과 삭제) · `27th/`(튜닝 모니터링 — 진행률·히스토리·export) · `28th/`(모델 상태·다운로드·모델 상세·다중 파이프라인) ·
`29th/`(F9 리소스/모니터링 세부설정) · `30th/`(F10 RAG 추가학습) · `31st/`(F11 다중 런타임 export) ·
`32nd/`(F12 평가지표 가이드) · `33rd~34th/`(frontend F9~F12 연동) · `35th/`(F9 실제 큐잉) ·
`36th/`(ops cron 배선) · `37th/`(잡 진행 WebSocket 스트리밍) ·
`38th/`(frontend Vitest/Playwright 배선 + F11 실 MLX export) · `39th/`(증강 — 패러프레이즈) ·
`40th/`(원스톱 파이프라인 스크립트, 수동 E2E) ·
`41st/`(F13 데이터셋 다운로드+manifest · F14 출처 필수화 · F15 파이프라인 run 추적) ·
`42nd/`(검수 큐 그룹핑 — 그룹→세부→레코드 3단계·그룹 요약) ·
`43rd/`(그룹 일괄 승인/반려 — 개별 검수 공존) · `44th/`(레코드 내용 div 팝업 모달) ·
`45th~50th/`(Survey P0+P1 고도화 v0.4 — E13 벤치·평가 연동 / E14 jailbreak·KTO / E15 디컨탬·DPI /
E16 lora_variant·mlx 플랜 / E17 DOC_PARSER / E18 커버리지 합성) —
전부 PASS (백엔드 169건 + frontend 9건 + E2E).

## 트러블슈팅

- 스키마 변경 후 잡 생성 등 500(`no such column`): dev `local.db` 는 `create_all` 이 컬럼을
  추가하지 않음 — `rm SecuFTPL/local.db` 후 재기동으로 재생성(개발 DB). 운영은 alembic migration.
- `Converting circular structure to JSON (Window)` @ /pipeline: 클릭 이벤트가 advance 인자로
  유입되던 결함 — 콜사이트 래핑 + StepStatus 강제로 수정(23차).
- ⑥ 평가 게이트 지표 미채움: 승인 레코드가 문서(needs_annotation)뿐이면 자동 행 0건 —
  기본 샘플로 채워지며, 검수에서 정답(JSON) 작성 후 "지표 자동 채우기"로 갱신.
  위저드 상태는 sessionStorage 로 새로고침에도 유지됨.
- 프론트 변경이 화면에 반영 안 될 때: `make local-restart` + 브라우저 강력 새로고침.
- 위저드 ② "수집 → 자동 다음" 미이동: 동일 내용 재수집이 완전중복 스킵(queued=0)된 경우 —
  현재는 전건 완전중복(데이터 기존재)이면 목표 충족으로 보고 자동 진행.
- 데이터셋 수집 422 (`List should have at least 1 item`): 빈 입력 전송이 원인이었음 —
  현재는 task_type 선택 시 템플릿 자동 채움 + 빈 입력 시 API 미호출 안내로 방지.
- `[Errno 48] Address already in use`: 다른 프로세스가 `API_PORT` 점유 — `lsof -nP -iTCP:8000 -sTCP:LISTEN` 으로
  확인 후 `.env.local` 의 `API_PORT` 변경(하드코딩 없음, env 만 수정하면 됨).
- Makefile 변수에 인라인 주석 금지: `VAR ?= value  # 주석` 은 trailing space 가 값에 포함되어 `ifeq` 비교가 깨짐.
- `VIRTUAL_ENV does not match` 경고: 상위 워크스페이스 venv 활성 상태 — uv 가 프로젝트 `.venv` 를 쓰므로 무해.
- `make test` exit 5(no tests): 스캐폴드 직후 상태 — impl/1st 이후 테스트 존재.
- pm2 미동작: Node 필요(`npx pm2`). Node 없으면 `PROC_MGR=honcho make local-all`.

## 다음 단계 (PRD 잔여)

- ~~E1~E8 전체 완료~~ — 데이터셋 코어 → 모델 레지스트리 → 튜닝·평가 리더보드 → 증강 →
  Agent 환류 → 야간 배치 → **독립 frontend**(`frontend/`) → Supervisor UI·CLI
- ~~F9 리소스/모니터링 세부설정~~ — 튜닝 시작 500건 게이트(`DATASET_MIN_RECORDS`) + 잡별
  GPU/VRAM 상한(`max_gpu`/`max_vram_gb`) + 실시간 리소스 모니터링(`GET /jobs/{id}/resources`) 완료
- ~~F10 RAG 기반 추가학습·모델 업그레이드~~ — `/api/v1/rag/synthesize`·`/upload`(합성 QA →
  검수 큐) + `/api/v1/rag/upgrade`(continual fine-tuning, `continual_from_job_id`) 완료
- ~~F11 다중 런타임 배포·풀모델 export~~ — `export?format=full`(어댑터 merge) +
  `export-plan?target=gguf|mlx`(Ollama/llama.cpp/MLX 변환 명령 플랜) 완료
- ~~F12 평가지표 가이드·추천~~ — `GET /tuning/eval-guide`(task_type·표본규모 기반 추천) 완료
- ~~frontend F9·F11·F12 연동~~ — tuning 페이지(리소스 입력·모니터링·어댑터/풀모델 다운로드·
  GGUF/MLX 플랜), leaderboard 페이지(평가지표 가이드 패널) 완료(impl/33rd)
- ~~frontend F10 RAG 페이지~~ — `/rag` 신규 페이지(코퍼스 합성 텍스트/파일 업로드 + 모델 업그레이드
  제출), 사이드바 내비게이션 추가 완료(impl/34th). **PRD F9~F12 백엔드+프런트 전체 완료**
- ~~리소스 상한 초과 시 실제 큐잉~~ — `TOTAL_GPU_CAPACITY` 기반 `admit_or_queue`/`dispatch_next_queued`
  (상한 내 즉시 시작, 초과 시 queued 유지 → 다른 잡 완료 시 FIFO 재시도) 완료(impl/35th). 동시에
  배치(`/batch/run`)가 잡을 생성만 하고 디스패치하지 않던 결함도 함께 수정
- ~~WebSocket 진행 스트리밍~~ — `WS /jobs/{id}/stream`(0.3초 주기 push, tuning 페이지가 running
  잡마다 구독) 완료(impl/37th). 장시간 잡용 외부 큐(arq/celery, 다중 프로세스/노드 확장 시 필요)는
  현재 단일 프로세스 인메모리 디스패처(F9 §7.12)로 충분해 미구현
- ~~frontend 자동화 시험(Vitest/Playwright) 배선~~ — `frontend/vitest.config.mts`(단위 7건)·
  `playwright.config.ts`(e2e 2건), `make front-test`·`front-test-e2e` 완료(impl/38th)
- ~~F11 MLX 실 변환 실행~~ — `mlx-lm`(Apple Silicon, `uv sync --extra mlx`) 로
  `POST /jobs/{id}/export/mlx` 실행 경로 완료(impl/38th, 실 공개 테스트 모델로 검증).
  GGUF(llama.cpp)는 여전히 명령 플랜만(§7.14) — 리포지토리 클론·빌드가 필요해 범위 밖
- **잔여(GPU/Linux 환경 필요 — `.docs/GPU-실학습-배포-가이드.md` 참조)**: vLLM 서빙, 실 QLoRA
  학습(torch/transformers/peft/trl+bitsandbytes+CUDA — **설치 전 `_real_available()` 자동전환
  위험 때문에 `FORCE_TRAINING_MODE` 플래그 선행 필요**, 가이드 §2.2), llama.cpp 실 GGUF 변환,
  vLLM AWQ/GPTQ 양자화, 서빙 어댑터 실교체(ollama 연동), frontend 디자인 시스템(`/ui-design`)
- ~~증강 LLM 백엔드(패러프레이즈)~~ — `method: paraphrase`(LLM 문장 재구성, Ollama) 완료(impl/39th).
  역번역·키워드 치환과 함께 §7.4 증강 표 3항목 전부 구현 완료
- ~~ops cron 배선~~ — `GET /api/v1/batch/cron-plan`(`secuftpl batch cron-plan` CLI 동일) 로
  `FT_TRIGGER_SCHEDULE_CRON`·`HF_POLLING_CRON` crontab 라인 생성 완료(impl/36th). **자동 설치는
  하지 않음** — ops가 출력을 `crontab -e`로 직접 반영
- ~~F13~F15 데이터셋 export·출처 필수화·run 추적(E12)~~ — `GET /datasets/export`(+manifest zip)·
  `/runs`, 게이트③ `rejected_attribution`, 채널별 자동 스탬핑, CLI `dataset export/--input·runs·
  backfill-attribution` 완료(impl/41st). **운영 반영 시 1회**: 레거시 레코드 출처 태깅
  `uv run secuftpl dataset backfill-attribution --apply`
