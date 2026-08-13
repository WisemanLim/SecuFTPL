#!/usr/bin/env bash
set -euo pipefail

# Security LLM model downloader for macOS
# Default: dry-run for the practical pilot profile.
# Requires: Homebrew, Python 3.10+, git-lfs, and huggingface_hub CLI.
# Usage:
#   ./download_security_llm_models_macos.sh --profile pilot --dry-run
#   HF_TOKEN=hf_xxx ./download_security_llm_models_macos.sh --profile pilot --execute
#   HF_TOKEN=hf_xxx ./download_security_llm_models_macos.sh --profile core --execute
#   HF_TOKEN=hf_xxx ./download_security_llm_models_macos.sh --profile all --execute
#
# NOTE:
# - Some repositories are gated (e.g., Meta Llama) and require accepting the model license
#   in Hugging Face before this script can download them.
# - "all" is intentionally large and can require multiple TB. Start with pilot/core.
# - Pin each downloaded snapshot revision in the generated manifest before air-gap transfer.

PROFILE="pilot"
MODE="dry-run"
OUT_DIR="${OUT_DIR:-$PWD/security-llm-models}"
LOG_DIR="${LOG_DIR:-$PWD/logs}"
MAX_WORKERS="${MAX_WORKERS:-8}"
EXCLUDE_PATTERNS="${EXCLUDE_PATTERNS:-*.gguf *.onnx *.tflite *original*}"

usage() {
  cat <<'EOF'
Usage: download_security_llm_models_macos.sh [options]

Options:
  --profile pilot|core|all  Download tier (default: pilot)
  --output DIR              Destination root (default: ./security-llm-models)
  --workers N               Concurrent workers passed to hf download (default: 8)
  --dry-run                 Print resolved plan only (default)
  --execute                 Download selected repositories
  --include-gguf            Do not exclude GGUF files (not recommended for fine-tuning)
  --help                    Show this help

Profiles:
  pilot : 12 practical models for initial benchmark/SFT
  core  : 28 primary generative, code, multimodal, and cyber models
  all   : 44 models including encoder baselines; can consume multiple TB
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile) PROFILE="$2"; shift 2 ;;
    --output) OUT_DIR="$2"; shift 2 ;;
    --workers) MAX_WORKERS="$2"; shift 2 ;;
    --dry-run) MODE="dry-run"; shift ;;
    --execute) MODE="execute"; shift ;;
    --include-gguf) EXCLUDE_PATTERNS="*.onnx *.tflite *original*"; shift ;;
    --help|-h) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage; exit 2 ;;
  esac
done

case "$PROFILE" in pilot|core|all) ;; *) echo "Invalid profile: $PROFILE" >&2; exit 2 ;; esac

command -v python3 >/dev/null || { echo "python3 is required" >&2; exit 1; }
command -v git >/dev/null || { echo "git is required" >&2; exit 1; }

if ! command -v hf >/dev/null; then
  echo "Missing Hugging Face CLI. Install with:" >&2
  echo "  python3 -m pip install --upgrade 'huggingface_hub[cli]'" >&2
  exit 1
fi

mkdir -p "$OUT_DIR" "$LOG_DIR"

# Columns: profile|model_id|role|notes
# Models are official/original repositories where possible. Verify current model cards,
# licenses, and revisions before production or air-gapped transfer.
MODELS=$(cat <<'EOF'
pilot|Qwen/Qwen3-14B|gen|Primary Korean/English SOC-CTI candidate
pilot|Qwen/Qwen3-32B|gen|Higher-quality general candidate
pilot|Qwen/Qwen2.5-7B-Instruct|gen|24GB-GPU baseline
pilot|Qwen/Qwen2.5-14B-Instruct|gen|Stable general instruct baseline
pilot|Qwen/Qwen2.5-Coder-14B-Instruct|code|Code-security baseline
pilot|google/gemma-3-12b-it|vision|Multimodal phishing-document candidate
pilot|LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct|gen|Korean enterprise candidate
pilot|meta-llama/Llama-3.1-8B-Instruct|gen|Gated English baseline
pilot|RedHatAI/Foundation-Sec-8B|cyber-gen|Cybersecurity continued-pretraining base
pilot|fdtn-ai/Foundation-Sec-8B-Reasoning|cyber-gen|Cybersecurity reasoning comparison
pilot|jackaduma/SecBERT|encoder|Cybersecurity text encoder
pilot|ehsanaghaei/SecureBERT|encoder|Cybersecurity RoBERTa encoder
core|Qwen/Qwen3-8B|gen|Efficient general candidate
core|Qwen/Qwen3-30B-A3B|gen|MoE throughput candidate
core|Qwen/Qwen2.5-32B-Instruct|gen|Mid-large general instruct
core|Qwen/Qwen2.5-72B-Instruct|gen|Teacher/evaluation candidate
core|Qwen/Qwen2.5-Coder-7B-Instruct|code|Small code baseline
core|Qwen/Qwen2.5-Coder-32B-Instruct|code|Large code-security candidate
core|meta-llama/Llama-3.1-70B-Instruct|gen|Gated teacher/evaluation candidate
core|meta-llama/Llama-3.2-3B-Instruct|gen|Small routing/extraction candidate
core|meta-llama/Llama-3.3-70B-Instruct|gen|Gated high-quality English candidate
core|google/gemma-3-4b-it|vision|Small multimodal candidate
core|google/gemma-3-27b-it|vision|Large multimodal candidate
core|google/gemma-2-9b-it|gen|General baseline
core|google/gemma-2-27b-it|gen|Large general baseline
core|mistralai/Mistral-Nemo-Instruct-2407|gen|12B long-context candidate
core|mistralai/Mistral-Small-3.1-24B-Instruct-2503|vision|24B multimodal candidate
core|mistralai/Ministral-8B-Instruct-2410|gen|Small efficient candidate
core|mistralai/Mixtral-8x7B-Instruct-v0.1|gen|MoE candidate
core|CohereForAI/aya-expanse-8b|gen|Multilingual candidate
core|CohereForAI/aya-expanse-32b|gen|Large multilingual candidate
core|LGAI-EXAONE/EXAONE-3.5-32B-Instruct|gen|Large Korean candidate
core|microsoft/phi-4|gen|Reasoning comparison candidate
core|allenai/OLMo-2-7B-Instruct|gen|Open research candidate
core|allenai/OLMo-2-13B-Instruct|gen|Open research candidate
core|tiiuae/Falcon3-10B-Instruct|gen|General baseline
core|DeepSeek-AI/deepseek-coder-6.7b-instruct|code|Code baseline
core|deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct|code|MoE code candidate
core|microsoft/codebert-base|encoder|Code representation baseline
core|microsoft/graphcodebert-base|encoder|Code graph representation baseline
core|microsoft/unixcoder-base|encoder|Code representation/generation baseline
core|cisco-ai/SecureBERT2.0-base|encoder|Updated cyber encoder
core|SynamicTechnologies/CYBERT|encoder|Cybersecurity RoBERTa encoder
core|kumarrohit1707/CYBER-BERT|encoder|Cybersecurity BERT baseline
core|markusbayer/CySecBERT|encoder|Cybersecurity encoder comparison
core|ZySec-AI/SecurityLLM|cyber-gen|Cybersecurity instruct comparison
core|WhiteRabbitNeo/Llama-3-WhiteRabbitNeo-8B-v2.0|cyber-gen|Offensive/defensive comparison; restricted evaluation only
all|Qwen/Qwen2.5-Coder-32B|code-base|Base model for CPT/SFT experiments
all|deepseek-ai/DeepSeek-Coder-V2-Instruct|code|Large MoE code candidate
all|mistralai/Codestral-22B-v0.1|code|Code model; review license before use
all|microsoft/Phi-3.5-mini-instruct|gen|Small model baseline
all|RedHatAI/Meta-Llama-3.1-8B-Instruct-quantized.w4a16|gen-quant|Quantized inference comparison only
all|d4r1us007/llama-3.1-8b-instruct-cybersecurity|cyber-gen|Community derivative; evaluate provenance before use
all|Canstralian/pentest_ai|cyber-gen|Community security model; isolated evaluation only
all|microsoft/codebert-base-mlm|encoder|Masked-LM code baseline
all|microsoft/codebert-base-mlm|encoder|Duplicate-safe code baseline
all|microsoft/CodeBERTa-small-v1|encoder|Small code encoder
all|microsoft/CodeBERTa-language-id|encoder|Code language ID baseline
all|microsoft/CodeBERTa-small-v1|encoder|Duplicate-safe small code encoder
EOF
)

# Deduplicate model IDs while preserving the lowest profile tier where listed.
profile_rank() {
  case "$1" in pilot) echo 1 ;; core) echo 2 ;; all) echo 3 ;; esac
}
selected_rank=$(profile_rank "$PROFILE")

printf '%s\n' "$MODELS" | awk -F'|' -v max_rank="$selected_rank" '
function rank(p) { return p=="pilot" ? 1 : p=="core" ? 2 : 3 }
rank($1) <= max_rank && !seen[$2]++ { print }
' > "$LOG_DIR/model-plan.tsv"

COUNT=$(wc -l < "$LOG_DIR/model-plan.tsv" | tr -d ' ')
echo "Profile: $PROFILE"
echo "Mode: $MODE"
echo "Models selected: $COUNT"
echo "Output directory: $OUT_DIR"
echo
column -t -s '|' "$LOG_DIR/model-plan.tsv" || cat "$LOG_DIR/model-plan.tsv"

if [[ "$MODE" == "dry-run" ]]; then
  echo
  echo "Dry run complete. Re-run with --execute after reviewing licenses, storage, and model-card revisions."
  exit 0
fi

if [[ -z "${HF_TOKEN:-}" ]]; then
  echo "HF_TOKEN is not set. Public models may download, but gated models will fail." >&2
  echo "For gated models, accept the model license in the Hugging Face UI and export HF_TOKEN=hf_..." >&2
fi

MANIFEST="$OUT_DIR/download-manifest-$(date +%Y%m%d-%H%M%S).tsv"
printf 'model_id\trole\tnotes\tstatus\tlocal_dir\trevision\n' > "$MANIFEST"

while IFS='|' read -r tier model_id role notes; do
  safe_name="${model_id//\//__}"
  local_dir="$OUT_DIR/$safe_name"
  log_file="$LOG_DIR/${safe_name}.log"

  echo
  echo "==> Downloading $model_id ($role)"

  # shellcheck disable=SC2086
  if hf download "$model_id" \
      --repo-type model \
      --local-dir "$local_dir" \
      --local-dir-use-symlinks False \
      --max-workers "$MAX_WORKERS" \
      --exclude $EXCLUDE_PATTERNS \
      ${HF_TOKEN:+--token "$HF_TOKEN"} >"$log_file" 2>&1; then

    revision=$(git -C "$local_dir" rev-parse HEAD 2>/dev/null || echo "snapshot-no-git")
    printf '%s\t%s\t%s\t%s\t%s\t%s\n' \
      "$model_id" "$role" "$notes" "OK" "$local_dir" "$revision" >> "$MANIFEST"
    echo "OK: $model_id"
  else
    printf '%s\t%s\t%s\t%s\t%s\t%s\n' \
      "$model_id" "$role" "$notes" "FAILED" "$local_dir" "" >> "$MANIFEST"
    echo "FAILED: $model_id (see $log_file)" >&2
  fi
done < "$LOG_DIR/model-plan.tsv"

find "$OUT_DIR" -type f -print0 | sort -z | xargs -0 shasum -a 256 > "$MANIFEST.sha256"
echo
echo "Download run complete."
echo "Manifest: $MANIFEST"
echo "SHA-256 manifest: $MANIFEST.sha256"
echo "Review FAILED rows and model-card licenses before air-gap transfer."
