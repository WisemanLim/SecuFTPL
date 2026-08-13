# SecuFTPL

> 🇰🇷 [한국어](README.md) | 🇺🇸 English

Security-domain LLM Fine-Tune Pipeline platform — security dataset construction
(collect·sanitize·augment) → multi-base-model fine-tuning → evaluation comparison →
agent feedback loop → nightly batch auto re-tuning & redeployment.

> **Scaffold**: `wise-dev-standard` / profile `python-fastapi` / domain `ict-saas` (+govtech·finance deltas)
> **Docs**: [PRD](.docs/SecuFTPL-PRD.md) · [COMPLIANCE.md](COMPLIANCE.md) · [Testing standard](test/README.md)

## Architecture / Directory

```
app/
├── main.py               # FastAPI entrypoint (lifespan: DB init, /supervisor UI)
├── cli.py                # secuftpl CLI — run pipelines without a frontend (F8)
├── web/
│   └── supervisor.html   # Supervisor pipeline test UI (F7, no login · internal network only)
├── core/
│   ├── config.py         # pydantic-settings (env-driven)
│   ├── db.py             # SQLAlchemy engine/session (DATABASE_URL)
│   └── schemas.py        # canonical sft-messages schema (PRD §7.2)
├── models/
│   ├── records.py        # dataset_records (review queue) · pseudonym_map
│   └── registry.py       # model_registry (base-model registry, F2)
├── services/
│   ├── gate.py           # gate: secret/internal-asset/prompt-injection scan (§7.3 ②④⑦)
│   ├── sanitize.py       # pseudonymization: stable tokens <KIND_0001> (§7.3 ⑤)
│   ├── dedup.py          # exact (sha256) & near (shingle Jaccard) dedup (§7.3 ⑥)
│   ├── formats.py        # F6 adapters + dpo-pairs/eval-set export
│   ├── catalog.py        # seed catalog pilot 12/core/all (mirrors download script)
│   ├── hf_registry.py    # seed·similarity·manifest·download plan (§7.5)
│   ├── model_download.py # model download worker: registered→downloading→downloaded (F2)
│   ├── augment.py        # E4 augmentation: keyword substitution (protected-ID guard)·lineage
│   ├── evaluate.py       # E3 eval runner: json_valid/severity/attack F1 (§5)
│   ├── tuning.py         # E3 job orchestration·QLoRA plan·leaderboard
│   ├── trainer.py        # training worker: background QLoRA (real/simulate auto)·auto-eval (§7.5)
│   └── batch.py          # E6 nightly batch: 3 trigger modes·evaluation gate·history
└── api/
    ├── datasets.py       # /api/v1/datasets — validate·convert·formats
    ├── records.py        # /api/v1/records — ingest·augment·queue·review
    ├── registry.py       # /api/v1/models — seed·pin·manifest·events/scan·download-plan
    ├── tuning.py         # /api/v1/tuning — jobs·plan·complete·evaluate·leaderboard·resources(F9)·export-plan(F11)·eval-guide(F12)
    ├── feedback.py       # /api/v1/feedback — agent feedback loop·stats (E5)
    ├── batch.py          # /api/v1/batch — should-run·run·gate·runs·cron-plan (E6)
    └── rag.py            # /api/v1/rag — synthesize·upload·upgrade (F10)
frontend/                 # E7 standalone Next.js app (wise-FP as reference only — no login)
├── app/                  # dashboard·pipeline (step wizard)·models·datasets·queue·tuning (resources·export F9/F11)·leaderboard (eval guide F12)·rag (corpus synthesis·model upgrade F10)
├── components/           # Shell (collapsible left sidebar)·Stepper (stage status cards)
├── lib/api.ts            # same-origin /api/* (rewrites proxy → FastAPI)
└── next.config.mjs       # NEXT_PUBLIC_API_BASE proxy config
# style: Genians CI green (#86BC25) — mirrors SeCuardian front (PRD §7.11)
test/                     # pytest + testing standard (dev-env/, impl/<Nth>/)
scripts/                 # run-pipeline.sh — one-stop pipeline orchestration (F8 extension)
.docs/                    # PRD, reference docs, model download scripts
```

## Stack

Python 3.12+ · FastAPI · uv · SQLAlchemy 2/Alembic · PostgreSQL 17 · Redis 7.4 ·
Docker Compose v2 · Helm(K8s) · GitHub Actions (uv sync→ruff→pytest)

## Prerequisites

- Python 3.12+, [uv](https://docs.astral.sh/uv/), Docker Desktop (Compose v2), GNU Make
- Node.js (default process manager pm2 runs via `npx` — alternative: `PROC_MGR=honcho`)
- (optional) `uv sync --extra mlx` — F11 real MLX export (Apple Silicon only, `mlx-lm`)
- (optional) frontend e2e tests: `cd frontend && pnpm exec playwright install chromium` (Vitest just needs `pnpm install` — already in devDependencies)
- Check: `make preflight`

## Environment (.env matrix)

| File | DB | Purpose |
|---|---|---|
| `.env.local` | sqlite (`sqlite:///./local.db`) | direct run, minimal deps |
| `.env.dev` | postgres (compose) | shared dev |
| `.env.staging` | postgres | prod-equivalent rehearsal |
| `.env.prod` | keys only | Vault/Secret Manager injection |

Operational options (PRD §7.9): `FT_TRIGGER_MODE=schedule` · `HF_EVENT_MODE=polling` (weekly) ·
`SATISFACTION_SCALE=binary` · `SERVING_STACK=ollama` · `DATASET_MIN_RECORDS=500` (tuning start gate) ·
`JOB_MAX_GPU=1`/`JOB_MAX_VRAM_GB=24` (default job resource limits, F9) ·
`TOTAL_GPU_CAPACITY=2` (system-wide concurrent training cap, queues jobs beyond it). Full keys: [.env.example](.env.example).
**Never commit real secrets** — `.gitignore` blocks `.env.*` (`!.env.example`).

## Run

```bash
uv sync && make front-install    # install dependencies (backend + frontend)
make local-all                   # ★ standard path: infra + web(api) + front together (pm2)
make ps / local-logs / local-stop
make dev-all / dev-build         # full dev stack in containers (api + front + infra, .env.dev)
# single-process debugging:
make dev                         # api only, foreground (uvicorn --reload)
make front-dev                   # front only (Next dev)
make up ENV=dev                  # infra only (postgres+redis)
```

`local-all` manages **web+front together** via ecosystem.config.cjs (pm2, default) or
Procfile.dev (`PROC_MGR=honcho`) — ports and API base come from `.env.<env>`
(`API_PORT`/`FRONT_PORT`/`BIND_HOST`).

## Ports

**Port SSOT (PRD §7.9)**: every listening port and bind IP has `.env.<env>` as its single source.
The Makefile injects it into honcho via `-e .env.$(ENV)` and into pm2 via `ENV_FILE=.env.$(ENV)` —
on a conflict, changing `API_PORT` in `.env.local` propagates to compose, Procfile, and pm2.

| Service | Port (default) | Note |
|---|---|---|
| API | `127.0.0.1:8000` | `API_PORT`, Swagger: `/docs`, **Supervisor UI: `/supervisor`** |
| Frontend (E7) | `127.0.0.1:3000` | `FRONT_PORT`; `/api/*` proxied via rewrites. **`/pipeline` = step wizard** (auto-advance·back navigation). In local-all and compose `front` (dev+) |
| PostgreSQL | `127.0.0.1:5432` | `POSTGRES_PORT` (compose) |
| Redis | `127.0.0.1:6379` | `REDIS_PORT` (compose) |
| Ollama (stub) | `127.0.0.1:11434` | uncomment in compose |

## API

| Method | Path | Description |
|---|---|---|
| GET | `/health` | health check |
| GET | `/api/v1/datasets/formats` | supported formats (canonical=sft-messages) |
| POST | `/api/v1/datasets/validate` | batch-validate canonical records (gate report) |
| POST | `/api/v1/datasets/convert` | format conversion (alpaca/sharegpt/openai-chat ↔ canonical; export: dpo-pairs·eval-set) |
| POST | `/api/v1/records/ingest` | ingest: gate → pseudonymize → dedup → queue as pending |
| POST | `/api/v1/records/upload` | **multi-file upload** — JSONL/JSON (F6 convert) + **documents PDF/DOCX/TXT/MD/HTML** (text extraction → needs_annotation record). UI directory picker uses this too |
| POST | `/api/v1/records/collect/dir` | server-path glob collection (CLI/ops) |
| POST | `/api/v1/records/collect/url` | **web collection** — whitelist + SSRF guard, response-type auto-detect (JSON=records / HTML=document), T3_untrusted |
| GET | `/api/v1/records/augment/suggestions` | **auto-suggested substitutions** — frequency × security synonym dictionary over approved records |
| GET | `/api/v1/records/queue?state=pending` | review queue listing (created_at=UTC ISO — rendered in browser locale) |
| GET | `/api/v1/records/{record_id}` | record detail (payload content for review) |
| DELETE | `/api/v1/records/{record_id}` | delete record — cascades to augmented children; UI confirms via popup |
| POST | `/api/v1/records/{record_id}/review` | approve/reject (`{"action":"approve\|reject","reviewer":"..."}`) — reject cascades to augmented children |
| POST | `/api/v1/models/seed` | seed catalog (`{"profile":"pilot\|core\|all"}`, idempotent) |
| GET | `/api/v1/models?status=&tier=` | registry listing (status: registered/downloading/downloaded/pinned…) |
| GET | `/api/v1/models/{model_id}/detail` | **model detail** — meta·status·download plan·snapshot manifest |
| POST | `/api/v1/models/{model_id}/download` | **download model** (background) — only downloaded is usable for training |
| POST | `/api/v1/models/{model_id}/pin` | pin revision (`{"revision":"<hash>"}`) — air-gap transfer basis |
| GET | `/api/v1/models/manifest` | pinned-model manifest |
| POST | `/api/v1/models/events/scan` | inject new-model events → similarity → candidate (ops scheduler calls on `HF_POLLING_CRON`) |
| GET | `/api/v1/models/{model_id}/download-plan` | generate hf CLI download command (never executed) |
| POST | `/api/v1/records/augment` | augmentation of approved originals → re-queue — `method: keyword` (dictionary) \| `backtranslate` (ko→en→ko) \| `paraphrase` (LLM sentence rewrite) — the latter two need Ollama, 503 when down |
| POST | `/api/v1/tuning/jobs` · GET `/jobs` | create tuning job (**422 if approved records < 500**; optional `max_gpu`/`max_vram_gb` — **stays queued** instead of starting immediately if it would exceed the system-wide cap `TOTAL_GPU_CAPACITY`)·list |
| GET | `/api/v1/tuning/jobs/{id}/resources` | **resource monitoring** (F9) — CPU/memory (real) + GPU util/VRAM (pynvml or simulated) |
| GET | `/api/v1/tuning/jobs/{id}/events` | poll training progress events (loss·steps) = history |
| WS | `/api/v1/tuning/jobs/{id}/stream` | **live streaming** (F9) — pushes status/progress/new events every 0.3s, sends a final snapshot and closes on succeeded/failed. Alternative to polling `/events` |
| GET | `/api/v1/tuning/jobs/{id}/export` | **model download** — `format=adapter`(default, tar.gz) \| `full` (merged full model, F11) |
| GET | `/api/v1/tuning/jobs/{id}/export-plan` | **runtime conversion plan** (F11) — `target=gguf`(Ollama/llama.cpp) \| `mlx` (Apple Silicon); command generation only, never executed |
| POST | `/api/v1/tuning/jobs/{id}/export/mlx` | **real MLX conversion** (F11) — actually runs the conversion when `mlx-lm` is installed (`uv sync --extra mlx`); 501 if not installed, 422 if the full model isn't real HF weights |
| POST | `/api/v1/tuning/jobs/{id}/retry` | re-run a queued/failed job (background re-dispatch) |
| DELETE | `/api/v1/tuning/jobs/{id}` | delete job (cascades event log; running blocked) |
| GET | `/api/v1/tuning/jobs/{id}/plan` | generate QLoRA training plan (YAML) |
| POST | `/api/v1/tuning/jobs/{id}/complete` | external worker callback (metrics → leaderboard) |
| GET | `/api/v1/tuning/leaderboard/detail/{model_id}` | **model detail** — evaluation history (eval_id) + tuning jobs |
| DELETE | `/api/v1/tuning/leaderboard/{eval_id}` | delete a single evaluation result (job·model kept) |
| GET | `/api/v1/tuning/eval-guide` | **eval metric guide/recommendation** (F12) — recommended metric set + guide text by `task_type`·`case_count` |
| GET | `/api/v1/tuning/eval-template` | auto-generate eval rows from approved records' answers (step ⑥ auto-fill) |
| POST | `/api/v1/tuning/evaluate` | evaluate prediction batch → leaderboard |
| GET | `/api/v1/tuning/leaderboard` | model comparison (sorted by attack_f1) |
| POST | `/api/v1/feedback` · GET `/feedback/stats` | agent Q/A + satisfaction feedback loop·stats (E5) |
| GET | `/api/v1/batch/should-run` · POST `/run` | batch trigger check·run (E6, called by ops cron) |
| POST | `/api/v1/batch/gate` · GET `/runs` | deployment gate (floors + regression check)·history |
| GET | `/api/v1/batch/cron-plan` | **ops cron wiring** — generates crontab lines for nightly batch·HF polling (never installed/executed; add via `crontab -e`) |
| POST | `/api/v1/rag/synthesize` · `/upload` | **RAG corpus → synthesized QA records** (F10) — chunk text/documents (PDF·DOCX·TXT·MD·HTML) → synthesize cause/resolution → queue for review |
| POST | `/api/v1/rag/upgrade` | **model upgrade** (F10) — submit a continual fine-tuning job on the approved (RAG-augmented) dataset; optional `continual_from_job_id` sets the base adapter |

```bash
curl -s localhost:8000/api/v1/datasets/convert -H 'content-type: application/json' -d '{
  "items": [{"instruction": "analyze alert", "output": "result"}],
  "source": "alpaca", "target": "canonical",
  "meta_defaults": {"record_id": "r-1", "dataset_version": "v0.1.0"}
}'
# → {"count":1,"items":[{"messages":[...],"metadata":{...}}]}

curl -s localhost:8000/api/v1/rag/synthesize -H 'content-type: application/json' -d '{
  "documents": [{"title": "threat-report-1", "text": "threat report body..."}],
  "task_type": "cti_extraction", "dataset_version": "v0.2.0"
}'
# → {"documents":1,"chunks":N,"ingest":{"queued":N,...}}  — approve, then call /rag/upgrade to train

curl -s localhost:8000/api/v1/tuning/jobs/ft-xxxx/export-plan?target=gguf
# → {"job_id":"ft-xxxx","target":"gguf","command":"python convert_hf_to_gguf.py ..."}
```

## Supervisor UI · CLI (F7·F8)

- **UI**: after `make dev`, open `http://127.0.0.1:8000/supervisor` — ① model selection (seed/pin/plan)
  ② purpose (task_type) ③ dataset JSONL validate·ingest·convert ④ review queue approve/reject
  ⑤ tuning run (enabled with E3). No login — **internal network only**; put an auth gateway in front for any exposure.
- **CLI**: for environments without a frontend — direct DB access, no API server needed.

```bash
uv run secuftpl dataset validate data.jsonl        # exit 1 on invalid (batch gate)
uv run secuftpl dataset convert in.jsonl --source alpaca --target canonical --out out.jsonl
uv run secuftpl dataset ingest data.jsonl && uv run secuftpl dataset queue
uv run secuftpl dataset review r-0001 --action approve --reviewer soc_01
uv run secuftpl models seed --profile pilot
uv run secuftpl models pin Qwen/Qwen3-14B --revision <hash>
uv run secuftpl models manifest
uv run secuftpl models scan discovered.jsonl
uv run secuftpl models download-plan Qwen/Qwen3-14B
uv run secuftpl dataset augment --substitutions '{"apache":"nginx"}'
uv run secuftpl tune create Qwen/Qwen3-14B --dataset-version v0.1.0
uv run secuftpl tune plan <job_id>                 # QLoRA plan → run on worker
uv run secuftpl tune evaluate preds.jsonl --model-id m --dataset-version v1
uv run secuftpl tune leaderboard
uv run secuftpl batch run                          # nightly batch (ops cron entrypoint)
uv run secuftpl batch gate <model_id> --dataset-version v1   # exit 1 when gate fails
```

## One-stop pipeline script (F8 extension)

`scripts/run-pipeline.sh` — runs model selection → dataset collection (gate·pseudonymization·
dedup) → review approval → (augmentation) → tuning job → eval gate → leaderboard comparison →
deploy (export) end-to-end over the HTTP API. Auto-starts the backend (same command as `make dev`)
if it isn't running, and stops it on completion (leaves an already-running server untouched).

```bash
make pipeline                          # or: ./scripts/run-pipeline.sh
RECORD_COUNT=1000 MODEL_ID=Qwen/Qwen3-32B ./scripts/run-pipeline.sh   # override options
AUGMENT_METHOD=backtranslate ./scripts/run-pipeline.sh                # needs Ollama
```

Key env vars: `MODEL_ID` (default `Qwen/Qwen3-14B`) · `DATASET_VERSION` (default auto-timestamped) ·
`RECORD_COUNT` (default 500, matches the `DATASET_MIN_RECORDS` gate — below it, the tuning step 422s) ·
`AUGMENT`/`AUGMENT_METHOD` (default `true`/`keyword`, offline) · `EXPORT_FORMAT` (default `adapter`) ·
`API_PORT` (default 8000). Each step's response is saved under `artifacts/pipeline-run-<timestamp>/`
as JSON/tar.gz. Requires: `curl`·`jq`·`uv`·`python3` (synthetic record generation, stdlib only).

## Test

```bash
make test           # uv run pytest (single test/ tree, backend 136 cases)
make front-test      # frontend Vitest unit tests (7 cases)
make front-test-e2e  # frontend Playwright e2e (2 cases, auto-starts dev server)
```

Iteration records: `test/dev-env/` · `test/impl/1st/` (E1 round 1) · `2nd/` (port SSOT) ·
`3rd/` (pseudonymization·dedup·review queue·DPO/eval export) · `4th/` (model registry) ·
`5th/` (Supervisor UI·CLI) · `6th/` (tuning·eval·leaderboard) · `7th/` (augmentation) ·
`8th/` (agent feedback) · `9th/` (nightly batch) · `10th/` (standalone frontend build·proxy E2E) ·
`11th/` (unified run — local-all=web+front, compose front) · `12th/` (UI revamp — green brand·
sidebar·pipeline wizard) · `13th/` (per-task JSONL auto-templates·empty-input guard) ·
`14th/` (review-queue record detail·locale time display) · `15th/` (collection channels — multi-file·
directory·URL, wise-FP A/B/C) · `16th/` (dataset deep-dive — document collection·user directory·
URL collection semantics·augment suggestions/back-translation) · `17th/` (review-queue delete —
lineage cascade·confirm popup) · `18th~19th/` (detail-panel actions next to status pill) ·
`20th/` (ingest auto-advance) · `21st/` (gate auto-filled metrics) · `22nd~23rd/` (wizard state
persistence·circular ref) · `24th/` (training worker background QLoRA·leaderboard detail) · `25th/` (job follow-up — retry·delete) · `26th/` (leaderboard-detail job actions·eval-result delete) · `27th/` (tuning monitoring — progress·history·export) · `28th/` (model status·download·detail·
multi-pipeline) · `29th/` (F9 resource/monitoring detail settings) · `30th/` (F10 RAG continued
training) · `31st/` (F11 multi-runtime export) · `32nd/` (F12 eval metric guide) ·
`33rd~34th/` (frontend F9~F12 wiring) · `35th/` (F9 real queuing) · `36th/` (ops cron wiring) ·
`37th/` (job progress WebSocket streaming) · `38th/` (frontend Vitest/Playwright wiring + F11
real MLX export) · `39th/` (augmentation — paraphrase) ·
`40th/` (one-stop pipeline script, manual E2E) —
all PASS (136 backend cases + 9 frontend cases + E2E).

## Troubleshooting

- 500 (`no such column`) after a schema change: dev `local.db` isn't altered by `create_all` —
  `rm SecuFTPL/local.db` and restart to recreate (dev DB). Use alembic migrations in production.
- `Converting circular structure to JSON (Window)` on /pipeline: a click event leaked into
  advance()'s mark argument — fixed by wrapping callsites + coercing to a valid StepStatus (impl/23rd).
- Step ⑥ gate metrics not auto-filled: if approved records are all documents (needs_annotation),
  zero rows are generated — a default sample is filled instead; annotate answers in review, then
  click "지표 자동 채우기". Wizard state now persists across refresh via sessionStorage.
- Frontend changes not visible: `make local-restart` + hard refresh.
- Wizard step ② "ingest → auto-next" not advancing: re-ingesting identical content was skipped as an
  exact duplicate (queued=0) — now all-duplicates counts as "data already present" and advances.
- Dataset ingest 422 (`List should have at least 1 item`): was caused by submitting an empty textarea —
  now the task_type picker auto-fills a template and empty input never reaches the API.
- `[Errno 48] Address already in use`: another process holds `API_PORT` — check with
  `lsof -nP -iTCP:8000 -sTCP:LISTEN`, then change `API_PORT` in `.env.local` (no hardcoding anywhere).
- No inline comments on Makefile variables: `VAR ?= value  # comment` embeds trailing spaces into the value and breaks `ifeq`.
- `VIRTUAL_ENV does not match` warning: parent workspace venv active — uv uses project `.venv`, harmless.
- `make test` exit 5 (no tests): fresh-scaffold state only — tests exist since impl/1st.
- pm2 not working: requires Node (`npx pm2`). Without Node: `PROC_MGR=honcho make local-all`.

## Next (PRD backlog)

- ~~E1~E8 all done~~ — dataset core → model registry → tuning·eval leaderboard → augmentation →
  agent feedback → nightly batch → **standalone frontend** (`frontend/`) → Supervisor UI·CLI
- ~~F9 resource/monitoring detail settings~~ — tuning-start 500-record gate (`DATASET_MIN_RECORDS`) +
  per-job GPU/VRAM limits (`max_gpu`/`max_vram_gb`) + live resource monitoring
  (`GET /jobs/{id}/resources`) done
- ~~F10 RAG-based continued training / model upgrade~~ — `/api/v1/rag/synthesize`·`/upload`
  (synthesize QA → review queue) + `/api/v1/rag/upgrade` (continual fine-tuning,
  `continual_from_job_id`) done
- ~~F11 multi-runtime deploy + full-model export~~ — `export?format=full` (adapter merge) +
  `export-plan?target=gguf|mlx` (Ollama/llama.cpp/MLX conversion command plan) done
- ~~F12 eval metric guide/recommendation~~ — `GET /tuning/eval-guide`
  (task_type·sample-size based recommendation) done
- ~~frontend F9·F11·F12 wiring~~ — tuning page (resource inputs·monitoring·adapter/full-model
  download·GGUF/MLX plan), leaderboard page (eval guide panel) done (impl/33rd)
- ~~frontend F10 RAG page~~ — new `/rag` page (corpus synthesis via text/file upload + model
  upgrade submission), sidebar nav entry added (impl/34th). **PRD F9~F12 backend + frontend fully done**
- ~~real queuing when resource limits are exceeded~~ — `TOTAL_GPU_CAPACITY`-based
  `admit_or_queue`/`dispatch_next_queued` (start immediately within capacity, stay queued when over
  → FIFO retry when another job finishes) done (impl/35th). Also fixed a bug where batch
  (`/batch/run`) created jobs but never dispatched them
- ~~WebSocket progress streaming~~ — `WS /jobs/{id}/stream` (pushes every 0.3s, tuning page
  subscribes per running job) done (impl/37th). External queue (arq/celery, needed for
  multi-process/multi-node scale) not implemented — the current single-process in-memory
  dispatcher (F9 §7.12) is sufficient for now
- ~~frontend automated tests (Vitest/Playwright) wiring~~ — `frontend/vitest.config.mts` (7 unit
  tests) · `playwright.config.ts` (2 e2e tests), `make front-test`·`front-test-e2e` done (impl/38th)
- ~~F11 real MLX conversion~~ — `mlx-lm` (Apple Silicon, `uv sync --extra mlx`) powers
  `POST /jobs/{id}/export/mlx` done (impl/38th, verified with a real public test model). GGUF
  (llama.cpp) is still plan-only (§7.14) — needs cloning/building the repo, out of scope here
- **Remaining (needs a GPU/Linux environment — see `.docs/GPU-실학습-배포-가이드.md`)**: vLLM
  serving, real QLoRA training (torch/transformers/peft/trl+bitsandbytes+CUDA — **installing
  these first requires a `FORCE_TRAINING_MODE` flag** to avoid `_real_available()` silently
  flipping the whole test suite to real mode, guide §2.2), real GGUF conversion (llama.cpp),
  vLLM AWQ/GPTQ quantization, live adapter swap (ollama), frontend design system (`/ui-design`)
- ~~LLM augmentation backend (paraphrase)~~ — `method: paraphrase` (LLM sentence rewrite, Ollama)
  done (impl/39th). All three augmentation techniques in §7.4 (keyword·back-translation·paraphrase)
  are now implemented
- ~~ops cron wiring~~ — `GET /api/v1/batch/cron-plan` (same as CLI `secuftpl batch cron-plan`)
  generates crontab lines for `FT_TRIGGER_SCHEDULE_CRON`·`HF_POLLING_CRON` done (impl/36th).
  **Never installs automatically** — ops applies the output via `crontab -e`
