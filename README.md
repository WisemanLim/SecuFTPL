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
    ├── tuning.py         # /api/v1/tuning — jobs·plan·complete·evaluate·leaderboard
    ├── feedback.py       # /api/v1/feedback — Agent 환류(만족도)·stats (E5)
    └── batch.py          # /api/v1/batch — should-run·run·gate·runs (E6)
frontend/                 # E7 독립 Next.js 앱 (wise-FP 참고만 — 로그인 없음)
├── app/                  # 대시보드·pipeline(단계별 위저드)·models·datasets·queue·tuning·leaderboard
├── components/           # Shell(좌측 접이식 사이드바)·Stepper(단계 상태 카드)
├── lib/api.ts            # same-origin /api/* (rewrites 프록시 → FastAPI)
└── next.config.mjs       # NEXT_PUBLIC_API_BASE 프록시 설정
# 스타일: Genians CI 그린(#86BC25) — SeCuardian front 준용 (PRD §7.11)
test/                     # pytest + 시험표준 (dev-env/, impl/<Nth>/)
.docs/                    # PRD·참고 문서·모델 다운로드 스크립트
```

## 기술 스택

Python 3.12+ · FastAPI · uv · SQLAlchemy 2/Alembic · PostgreSQL 17 · Redis 7.4 ·
Docker Compose v2 · Helm(K8s) · GitHub Actions(uv sync→ruff→pytest)

## 사전 요구사항

- Python 3.12+, [uv](https://docs.astral.sh/uv/), Docker Desktop(Compose v2), GNU Make
- Node.js (기본 프로세스 매니저 pm2 를 `npx` 로 실행 — 대안: `PROC_MGR=honcho`)
- 점검: `make preflight`

## 환경 설정 (.env 매트릭스)

| 파일 | DB | 용도 |
|---|---|---|
| `.env.local` | sqlite (`sqlite:///./local.db`) | 직접 실행, 외부 의존 최소 |
| `.env.dev` | postgres (compose) | 공유 개발 |
| `.env.staging` | postgres | prod 동등 리허설 |
| `.env.prod` | 키 목록만 | Vault/Secret Manager 주입 전제 |

운영 옵션(PRD §7.9): `FT_TRIGGER_MODE=schedule` · `HF_EVENT_MODE=polling`(주 1회) ·
`SATISFACTION_SCALE=binary` · `SERVING_STACK=ollama`. 전체 키는 [.env.example](.env.example).
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
| POST | `/api/v1/records/ingest` | 수집: 게이트→가명화→중복제거→pending 적재 |
| POST | `/api/v1/records/upload` | **파일(멀티) 업로드** — JSONL/JSON(F6 변환) + **문서 PDF/DOCX/TXT/MD/HTML**(텍스트 추출→주석 대기 레코드). UI 디렉토리 선택도 이 경로 |
| POST | `/api/v1/records/collect/dir` | 서버 경로 glob 수집 (CLI/ops 용) |
| POST | `/api/v1/records/collect/url` | **인터넷 수집** — 화이트리스트+SSRF 차단, 응답 유형 자동 판별(JSON=레코드/HTML=문서), T3_untrusted |
| GET | `/api/v1/records/augment/suggestions` | **치환 후보 자동 추천** — 승인 레코드 빈도×보안 동의어 사전 |
| GET | `/api/v1/records/queue?state=pending` | 검수 큐 조회 (created_at=UTC ISO — 화면 locale 변환) |
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
| POST | `/api/v1/records/augment` | 승인 원본 증강 → 큐 재편입 — `method: keyword`(치환 사전) \| `backtranslate`(ko→en→ko, Ollama 필요·미기동 503) |
| POST | `/api/v1/tuning/jobs` · GET `/jobs` | 튜닝 잡 생성(→**백그라운드 학습 즉시 시작**)·목록 |
| GET | `/api/v1/tuning/jobs/{id}/events` | 학습 진행 이벤트(손실·단계) 폴링 = 히스토리 |
| GET | `/api/v1/tuning/jobs/{id}/export` | **succeeded 모델(어댑터) tar.gz 다운로드** |
| POST | `/api/v1/tuning/jobs/{id}/retry` | queued/failed 잡 재실행(백그라운드 재투입) |
| DELETE | `/api/v1/tuning/jobs/{id}` | 잡 삭제(이벤트 로그 연쇄, running 차단) |
| GET | `/api/v1/tuning/jobs/{id}/plan` | QLoRA 학습 플랜(YAML) 생성 |
| POST | `/api/v1/tuning/jobs/{id}/complete` | 외부 worker 콜백 (지표 → 리더보드) |
| GET | `/api/v1/tuning/leaderboard/detail/{model_id}` | **모델 세부내용** — 평가 이력(eval_id) + 튜닝 잡 |
| DELETE | `/api/v1/tuning/leaderboard/{eval_id}` | 평가 결과 1건 삭제(잡·모델 유지) |
| GET | `/api/v1/tuning/eval-template` | 승인 레코드 정답에서 평가 지표 행 자동 생성 (⑥단계 자동 입력) |
| POST | `/api/v1/tuning/evaluate` | 예측 배치 평가 → 리더보드 반영 |
| GET | `/api/v1/tuning/leaderboard` | 모델 간 비교 (attack_f1 기본 정렬) |
| POST | `/api/v1/feedback` · GET `/feedback/stats` | Agent 질의/답변+만족도 환류·집계 (E5) |
| GET | `/api/v1/batch/should-run` · POST `/run` | 배치 트리거 판정·실행 (E6, ops cron 호출) |
| POST | `/api/v1/batch/gate` · GET `/runs` | 배포 게이트(하한+회귀 검사)·이력 |

```bash
curl -s localhost:8000/api/v1/datasets/convert -H 'content-type: application/json' -d '{
  "items": [{"instruction": "경보 분석", "output": "결과"}],
  "source": "alpaca", "target": "canonical",
  "meta_defaults": {"record_id": "r-1", "dataset_version": "v0.1.0"}
}'
# → {"count":1,"items":[{"messages":[...],"metadata":{...}}]}
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
uv run secuftpl tune create Qwen/Qwen3-14B --dataset-version v0.1.0
uv run secuftpl tune plan <job_id>                 # QLoRA 플랜 → worker 실행
uv run secuftpl tune evaluate preds.jsonl --model-id m --dataset-version v1
uv run secuftpl tune leaderboard
uv run secuftpl batch run                          # 야간 배치 (ops cron 진입점)
uv run secuftpl batch gate <model_id> --dataset-version v1   # 미통과 시 exit 1
```

## 테스트

```bash
make test        # uv run pytest (test/ 단일 트리, 17건)
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
`24th/`(학습 워커 백그라운드 QLoRA·리더보드 상세) · `25th/`(잡 후속처리 — 재실행·삭제) · `26th/`(리더보드 상세 잡 액션·평가 결과 삭제) · `27th/`(튜닝 모니터링 — 진행률·히스토리·export) · `28th/`(모델 상태·다운로드·모델 상세·다중 파이프라인) —
전부 PASS (백엔드 94건 + E2E).

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
- **잔여(확장 지점)**: 실학습 의존성(torch/transformers/peft/trl+GPU)은 worker 이미지에서 설치
  (코어는 미설치 시 시뮬레이션 자동), 장시간 잡용 외부 큐(arq/celery)·WebSocket 진행 스트리밍,
  서빙 어댑터 실교체(ollama 연동), 증강 LLM 백엔드(번역·패러프레이즈),
  ops cron 배선(`FT_TRIGGER_SCHEDULE_CRON`·`HF_POLLING_CRON`), frontend 디자인 시스템(`/ui-design`)
