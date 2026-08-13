#!/usr/bin/env bash
# secuftpl — 원스톱 파이프라인 스크립트 (PRD F8 확장, §7.10, impl/40th).
#
# 모델 선택 → 데이터셋 수집(게이트·가명화·중복제거) → 검수 승인 → (증강) →
# 튜닝 잡 → 평가 게이트 → 리더보드 비교 → 배포(export) 를 HTTP API 로 한 번에 실행한다.
# 백엔드가 미기동 상태면 `make dev` 와 동일한 명령으로 백그라운드 기동 후, 완료 시 자동 종료한다
# (스크립트 시작 전부터 이미 떠 있던 서버는 건드리지 않음).
#
# 사용법: scripts/run-pipeline.sh [옵션]
#   MODEL_ID, REVISION, DATASET_VERSION, TASK_TYPE, RECORD_COUNT, AUGMENT, AUGMENT_METHOD,
#   EXPORT_FORMAT, API_PORT, ARTIFACTS_DIR 환경변수로 조정 가능(아래 기본값 참고).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

API_PORT="${API_PORT:-8000}"
API="http://127.0.0.1:${API_PORT}"
MODEL_ID="${MODEL_ID:-Qwen/Qwen3-14B}"
REVISION="${REVISION:-pipeline$(date +%s)}"            # 데모용 dummy pin — 실 HF 커밋 해시 아님
DATASET_VERSION="${DATASET_VERSION:-pipeline-$(date +%Y%m%d%H%M%S)}"
TASK_TYPE="${TASK_TYPE:-alert_triage}"
RECORD_COUNT="${RECORD_COUNT:-500}"                    # DATASET_MIN_RECORDS 기본값과 동일(§7.5 게이트)
AUGMENT="${AUGMENT:-true}"
AUGMENT_METHOD="${AUGMENT_METHOD:-keyword}"             # keyword(오프라인) | backtranslate | paraphrase(둘 다 Ollama 필요)
EXPORT_FORMAT="${EXPORT_FORMAT:-adapter}"               # adapter(경량) | full(어댑터 merge)
ARTIFACTS_DIR="${ARTIFACTS_DIR:-$ROOT/artifacts/pipeline-run-$(date +%Y%m%d%H%M%S)}"

STARTED_SERVER=0
SERVER_PID=""

log() { echo "[$(date +%H:%M:%S)] $*" >&2; }
die() { log "FAIL: $*"; exit 1; }

require() { command -v "$1" >/dev/null 2>&1 || die "'$1' 미설치 — 설치 후 재시도"; }
require curl
require jq
require uv
require python3

cleanup() {
  if [ "$STARTED_SERVER" = "1" ] && [ -n "$SERVER_PID" ]; then
    log "백엔드 종료(pid $SERVER_PID) — 이 스크립트가 기동한 서버만 정리"
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

api() {  # api METHOD PATH [JSON_BODY]  — 실패 시 상세 출력 후 종료
  local method="$1" path="$2" body="${3:-}" res
  if [ -n "$body" ]; then
    res=$(curl -s -w '\n%{http_code}' -X "$method" "$API$path" -H 'content-type: application/json' -d "$body")
  else
    res=$(curl -s -w '\n%{http_code}' -X "$method" "$API$path")
  fi
  local code=${res##*$'\n'}
  local payload=${res%$'\n'*}
  if [ "$code" -ge 400 ]; then
    die "$method $path → $code: $payload"
  fi
  echo "$payload"
}

step() { log ""; log "=== $* ==="; }

# --- 0. 백엔드 기동 확인 / 필요 시 구동 ---
step "0/8 백엔드 상태 확인 ($API/health)"
if curl -sf "$API/health" >/dev/null 2>&1; then
  log "이미 실행 중 — 기존 서버 재사용(완료 후 종료하지 않음)"
else
  log "미기동 — 백그라운드 구동(make dev 와 동일 명령: uv run uvicorn)"
  mkdir -p "$ROOT/.make"
  nohup uv run uvicorn app.main:app --port "$API_PORT" > "$ROOT/.make/pipeline-api.log" 2>&1 &
  SERVER_PID=$!
  STARTED_SERVER=1
  ok=0
  for _ in $(seq 1 30); do
    if curl -sf "$API/health" >/dev/null 2>&1; then ok=1; break; fi
    sleep 1
  done
  [ "$ok" = "1" ] || die "백엔드 기동 실패 — $ROOT/.make/pipeline-api.log 확인"
  log "백엔드 기동 완료 (pid $SERVER_PID)"
fi

mkdir -p "$ARTIFACTS_DIR"
log "산출물 디렉터리: $ARTIFACTS_DIR"

# --- 1. 모델 선택 ---
step "1/8 모델 선택 — seed + pin ($MODEL_ID)"
api POST /api/v1/models/seed '{"profile":"pilot"}' >/dev/null
api POST "/api/v1/models/$MODEL_ID/pin" "{\"revision\":\"$REVISION\"}" | tee "$ARTIFACTS_DIR/01-model-pin.json"

# --- 2. 데이터셋 수집(게이트·가명화·중복제거는 서버측 기존 파이프라인이 그대로 적용) ---
step "2/8 데이터셋 수집 — 합성 레코드 ${RECORD_COUNT}건 ingest"
records_json=$(python3 - "$RECORD_COUNT" "$TASK_TYPE" "$DATASET_VERSION" <<'PYEOF'
import json
import sys

n, task_type, ds = int(sys.argv[1]), sys.argv[2], sys.argv[3]
records = [{
    "messages": [
        {"role": "user", "content": f"경보 pipeline-{i}: 아파치 웹서버에서 이상 행위 탐지(합성 레코드)"},
        {"role": "assistant", "content": json.dumps({
            "severity": "high" if i % 3 == 0 else "medium",
            "attack_mapping": [{"technique_id": "T1059.001", "name": "PowerShell",
                                 "evidence": f"synthetic pipeline record {i}"}],
            "unknowns": [], "citations": ["synthetic:pipeline"], "requires_human_approval": False,
        }, ensure_ascii=False)},
    ],
    "metadata": {"record_id": f"pipe-{ds}-{i}", "source_type": "manual",
                 "task_type": task_type, "dataset_version": ds},
} for i in range(n)]
print(json.dumps({"records": records}))
PYEOF
)
ingest_res=$(api POST /api/v1/records/ingest "$records_json")
echo "$ingest_res" > "$ARTIFACTS_DIR/02-ingest.json"
queued=$(echo "$ingest_res" | jq '.queued')
total=$(echo "$ingest_res" | jq '.total')
log "수집 결과: queued=$queued / total=$total (나머지는 중복/게이트 차단 — 02-ingest.json 참고)"
[ "$queued" -gt 0 ] || die "수집된 레코드가 없음(전건 중복/게이트 차단) — RECORD_COUNT 조정 후 재시도"

# --- 3. 검수 승인 ---
step "3/8 검수 승인 — queued ${queued}건 approve"
record_ids=$(echo "$ingest_res" | jq -r '.results[] | select(.status=="queued") | .record_id')
approved=0
for rid in $record_ids; do
  api POST "/api/v1/records/$rid/review" '{"action":"approve","reviewer":"pipeline-cli"}' >/dev/null
  approved=$((approved + 1))
done
log "승인 완료: ${approved}건"

# --- 4. 증강(선택) ---
if [ "$AUGMENT" = "true" ]; then
  step "4/8 증강 — method=$AUGMENT_METHOD"
  case "$AUGMENT_METHOD" in
    keyword)
      aug_body='{"method":"keyword","substitutions":{"아파치":"nginx"}}'
      ;;
    backtranslate|paraphrase)
      aug_body="{\"method\":\"$AUGMENT_METHOD\"}"
      log "주의: $AUGMENT_METHOD 는 Ollama(OLLAMA_BASE_URL) 필요 — 미기동 시 503으로 이 단계만 실패"
      ;;
    *) die "알 수 없는 AUGMENT_METHOD: $AUGMENT_METHOD (keyword|backtranslate|paraphrase)" ;;
  esac
  api POST /api/v1/records/augment "$aug_body" | tee "$ARTIFACTS_DIR/03-augment.json" | jq -c '{method, originals, augmented}'
else
  step "4/8 증강 — 건너뜀 (AUGMENT=false)"
fi

# --- 5. 튜닝 잡 ---
step "5/8 튜닝 잡 제출"
job=$(api POST /api/v1/tuning/jobs "{\"model_id\":\"$MODEL_ID\",\"dataset_version\":\"$DATASET_VERSION\"}")
echo "$job" > "$ARTIFACTS_DIR/04-job-create.json"
job_id=$(echo "$job" | jq -r '.job_id')
log "job_id=$job_id"

log "튜닝 잡 진행 대기(최대 60초, 시뮬레이션 모드면 즉시 완료)"
status="queued"
for _ in $(seq 1 60); do
  status=$(api GET "/api/v1/tuning/jobs" | jq -r --arg jid "$job_id" '.jobs[] | select(.job_id==$jid) | .status')
  case "$status" in succeeded|failed) break ;; esac
  sleep 1
done
log "튜닝 잡 최종 상태: $status"
if [ "$status" != "succeeded" ]; then
  die "튜닝 잡 미완료(status=$status) — queued 면 TOTAL_GPU_CAPACITY 리소스 상한 확인, failed 면 이벤트 로그(GET /jobs/$job_id/events) 확인"
fi

# --- 6. 평가 게이트 ---
step "6/8 평가 게이트"
gate=$(api POST /api/v1/batch/gate "{\"model_id\":\"$MODEL_ID\",\"dataset_version\":\"$DATASET_VERSION\"}")
echo "$gate" | tee "$ARTIFACTS_DIR/05-gate.json" | jq .
passed=$(echo "$gate" | jq -r '.passed')

# --- 7. 리더보드 비교 ---
step "7/8 리더보드"
api GET "/api/v1/tuning/leaderboard?dataset_version=$DATASET_VERSION" \
  | tee "$ARTIFACTS_DIR/06-leaderboard.json" | jq -c '.items[] | {model_id, baseline, attack_f1, json_valid_rate}'

# --- 8. 배포(게이트 통과 시에만) ---
step "8/8 배포"
if [ "$passed" = "true" ]; then
  deploy_path="$ARTIFACTS_DIR/deploy-$job_id-$EXPORT_FORMAT.tar.gz"
  curl -sf "$API/api/v1/tuning/jobs/$job_id/export?format=$EXPORT_FORMAT" -o "$deploy_path"
  log "배포 아티팩트 저장: $deploy_path"
else
  log "게이트 미통과($passed) — 배포 차단(§6 리스크: 미통과 시 이전 버전 유지)"
fi

log ""
log "파이프라인 완료 — 산출물: $ARTIFACTS_DIR"
