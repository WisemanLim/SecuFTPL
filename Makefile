# secuftpl — python-fastapi (정적 템플릿 / static scaffold template)
.PHONY: dev test build deploy up down dc-logs dc-ps ps preflight \
        local-all local-logs local-stop local-restart \
        dev-all dev-build dev-logs dev-stop dev-restart \
        staging-all staging-build staging-logs staging-stop staging-restart \
        prod-all prod-logs prod-stop prod-restart \
        local-down dev-down staging-down prod-down
ENV ?= local
ENV_FILE := $(wildcard .env.$(ENV))
DC := docker compose $(if $(ENV_FILE),--env-file $(ENV_FILE),)   # .env.$(ENV) 존재 시 포트/IP/계정 주입
# 프로세스 매니저: pm2(기본, 백그라운드 데몬 — npx로 실행, Node 필요) | honcho(대안, PROC_MGR=honcho)
# 주의: make 인라인 주석은 값에 trailing space 를 포함시켜 ifeq 비교를 깨뜨림 — 주석은 반드시 별도 줄에.
PROC_MGR ?= pm2
# 포트/IP SSOT: .env.$(ENV) — honcho 는 -e 로, pm2 는 ENV_FILE 로 주입 (PRD §7.9)
HONCHO   ?= uv run honcho -f Procfile.dev -e .env.$(ENV)
PM2      ?= ENV_FILE=.env.$(ENV) npx --yes pm2
HONCHO_PIDFILE := .make/honcho.pid
HONCHO_LOGFILE := .make/honcho.log
# local 모드에서 기동할 compose 서비스만 지정 (비워두면 전체 infra).
# SQLite 사용 시 postgres 불필요 → 예: LOCAL_INFRA=redis make local-all
LOCAL_INFRA ?=

## --- 사전 호환성 점검 / Preflight (env-init 전 실행 권장) ---
preflight:  ## 런타임·도구 버전 호환성 점검
	@echo "=== Preflight: python-fastapi ==="
	@command -v python3 >/dev/null 2>&1 || command -v python >/dev/null 2>&1 || (echo "FAIL: Python 미설치" && exit 1)
	@command -v uv     >/dev/null 2>&1 || (echo "FAIL: uv 미설치 — brew install uv 또는 curl -LsSf https://astral.sh/uv/install.sh | sh" && exit 1)
	@command -v docker >/dev/null 2>&1 || (echo "FAIL: Docker 미설치" && exit 1)
	@$(DC) version >/dev/null 2>&1 || (echo "FAIL: docker compose v2 필요 (docker-compose v1 아님)" && exit 1)
	@python3 -c "import sys; v=sys.version_info; exit(0 if v>=(3,11) else 1)" 2>/dev/null || \
	 python  -c "import sys; v=sys.version_info; exit(0 if v>=(3,11) else 1)" 2>/dev/null || \
	 (echo "FAIL: Python 3.11+ 필요 (현재: $$(python3 --version 2>/dev/null || python --version))" && exit 1)
	@uv --version | awk '{split($$2,v,"."); if(v[1]+0==0 && v[2]+0<4) print "WARN: uv " $$2 " — 0.4+ 권장"}'
	@if [ "$(PROC_MGR)" = "pm2" ]; then command -v node >/dev/null 2>&1 || echo "WARN: Node 미설치 — PROC_MGR=pm2 사용 시 필요 (npx pm2)"; fi
	@echo "=== Preflight OK ==="

## --- infra (DB/캐시, app 제외) ---
up:    ## docker infra 기동 (postgres/redis — app 컨테이너 제외)
	$(DC) up -d
down:  ## infra 전체 정리
	$(DC) --profile app down --remove-orphans

## --- docker-compose 공통 유틸 ---
dc-logs:  ## $(DC) 로그 추적 (SVC=<service> 로 특정 서비스 지정)
	$(DC) logs -f $(SVC)
dc-ps:    ## $(DC) 컨테이너 상태
	$(DC) ps

## --- local 직접 실행 (포그라운드, 단일 프로세스) ---
dev:    ## 단일 직접 실행 (포그라운드)
	uv run uvicorn app.main:app --reload
test:   ; uv run pytest
build:  ## app 이미지 빌드
	$(DC) --profile app build
deploy: ; helm upgrade --install secuftpl ./deploy/helm

ps:  ## 프로세스 매니저 상태 (pm2 status / honcho check)
ifeq ($(PROC_MGR),pm2)
	$(PM2) status
else
	$(HONCHO) check
endif

## --- local-all: infra + 멀티프로세스(web/worker) 한 번에 기동 ---
## PROC_MGR=pm2(기본): pm2 데몬 기동(ecosystem.config.cjs) — Node/npx 필요
## PROC_MGR=honcho(대안): 백그라운드 데몬화(nohup+pidfile) → local-logs/local-stop/local-restart 로 제어
local-all:      ## [local] infra(docker) + web/worker 일괄 기동 (백그라운드)
	$(DC) up -d $(LOCAL_INFRA)
	@mkdir -p .make
ifeq ($(PROC_MGR),pm2)
	$(PM2) start ecosystem.config.cjs
else
	@if [ -f $(HONCHO_PIDFILE) ] && kill -0 $$(cat $(HONCHO_PIDFILE)) 2>/dev/null; then \
	  echo "honcho 이미 실행 중 (pid $$(cat $(HONCHO_PIDFILE)))"; \
	else \
	  nohup $(HONCHO) start > $(HONCHO_LOGFILE) 2>&1 & echo $$! > $(HONCHO_PIDFILE); \
	  echo "honcho 백그라운드 기동 (pid $$(cat $(HONCHO_PIDFILE)), 로그: $(HONCHO_LOGFILE))"; \
	fi
endif
local-logs:     ## [local] 통합 로그 추적 (Ctrl-C 로 tail 종료 — 프로세스는 유지)
ifeq ($(PROC_MGR),pm2)
	$(PM2) logs
else
	@touch $(HONCHO_LOGFILE) && tail -f $(HONCHO_LOGFILE)
endif
local-stop:     ## [local] web/worker 중지 + infra 정리
ifeq ($(PROC_MGR),pm2)
	$(PM2) delete ecosystem.config.cjs || true
else
	@if [ -f $(HONCHO_PIDFILE) ]; then kill $$(cat $(HONCHO_PIDFILE)) 2>/dev/null || true; rm -f $(HONCHO_PIDFILE); fi
endif
	$(DC) down --remove-orphans
local-restart:  ## [local] web/worker 재기동 (infra 유지)
ifeq ($(PROC_MGR),pm2)
	$(PM2) restart ecosystem.config.cjs
else
	@if [ -f $(HONCHO_PIDFILE) ]; then kill $$(cat $(HONCHO_PIDFILE)) 2>/dev/null || true; rm -f $(HONCHO_PIDFILE); fi
	nohup $(HONCHO) start > $(HONCHO_LOGFILE) 2>&1 & echo $$! > $(HONCHO_PIDFILE)
	@echo "honcho 재기동 (pid $$(cat $(HONCHO_PIDFILE)))"
endif

## --- dev: Docker 전체 스택 (.env.dev) ---
dev-all:      ## [dev] infra + app 컨테이너 기동 (기존 이미지 사용)
	docker compose --env-file .env.dev --profile app up -d
dev-build:    ## [dev] 이미지 빌드 후 기동 (코드 변경 후 재빌드 포함)
	docker compose --env-file .env.dev --profile app up -d --build
dev-logs:     ## [dev] 컨테이너 로그 추적 (SVC=<service>)
	docker compose --env-file .env.dev --profile app logs -f $(SVC)
dev-stop:     ## [dev] app + infra 전체 정리
	docker compose --env-file .env.dev --profile app down --remove-orphans
dev-restart:  ## [dev] 컨테이너 재기동 (SVC=<service>, 비우면 전체)
	docker compose --env-file .env.dev --profile app restart $(SVC)

## --- staging: Docker 전체 스택 (.env.staging) ---
staging-all:      ## [staging] infra + app 컨테이너 기동
	docker compose --env-file .env.staging --profile app up -d
staging-build:    ## [staging] 이미지 빌드 후 기동
	docker compose --env-file .env.staging --profile app up -d --build
staging-logs:     ## [staging] 컨테이너 로그 추적 (SVC=<service>)
	docker compose --env-file .env.staging --profile app logs -f $(SVC)
staging-stop:     ## [staging] app + infra 전체 정리
	docker compose --env-file .env.staging --profile app down --remove-orphans
staging-restart:  ## [staging] 컨테이너 재기동 (SVC=<service>, 비우면 전체)
	docker compose --env-file .env.staging --profile app restart $(SVC)

## --- prod: Docker 전체 스택 (.env.prod) ---
prod-all:      ## [prod] infra + app 컨테이너 기동
	docker compose --env-file .env.prod --profile app up -d
prod-logs:     ## [prod] 컨테이너 로그 추적 (SVC=<service>)
	docker compose --env-file .env.prod --profile app logs -f $(SVC)
prod-stop:     ## [prod] app + infra 전체 정리
	docker compose --env-file .env.prod --profile app down --remove-orphans
prod-restart:  ## [prod] 컨테이너 재기동 (SVC=<service>, 비우면 전체)
	docker compose --env-file .env.prod --profile app restart $(SVC)

## --- frontend (SecuFTPL 독립 Next.js — PRD E7) ---
front-install:  ## [front] pnpm install
	cd frontend && pnpm install
front-dev:      ## [front] Next.js dev 서버 (FRONT_PORT 기본 3000 — API 는 rewrites 프록시)
	cd frontend && pnpm dev
front-build:    ## [front] 프로덕션 빌드 (타입 체크 포함)
	cd frontend && pnpm build

## --- 하위호환 별칭 / backward-compat aliases (recipe 없이 선행 타겟만 실행) ---
local-down:      local-stop      ## [local] local-stop 별칭 (하위호환)
dev-down:        dev-stop        ## [dev] dev-stop 별칭 (하위호환)
staging-down:    staging-stop    ## [staging] staging-stop 별칭 (하위호환)
prod-down:       prod-stop       ## [prod] prod-stop 별칭 (하위호환)
