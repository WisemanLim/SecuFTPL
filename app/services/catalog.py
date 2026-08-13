"""secuftpl — 베이스모델 시드 카탈로그 (PRD F2, E2).

근거: .docs/download_security_llm_models_macos.sh 의 MODELS 목록(tier|model_id|role|notes).
라이선스는 추측하지 않는다 — 모델카드 확인 전 None (gated 여부 포함 배포 전 검토).
"""
import re

# tier|model_id|role|notes — 스크립트와 동일 순서, 중복 model_id 는 최저 tier 우선
_RAW = """\
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
all|microsoft/CodeBERTa-small-v1|encoder|Small code encoder
all|microsoft/CodeBERTa-language-id|encoder|Code language ID baseline
"""

TIER_RANK = {"pilot": 1, "core": 2, "all": 3}

_PARAM_RE = re.compile(r"(\d+(?:\.\d+)?)\s*[bB]\b")
_FAMILY_RE = re.compile(r"^[A-Za-z]+")


def infer_family(model_id: str) -> str:
    """이름부 선두 알파벳 토큰 → 소문자 계열명 (Qwen/Qwen3-14B→qwen, meta-llama/Llama-3.1-8B→llama)."""
    name = model_id.split("/")[-1]
    m = _FAMILY_RE.match(name)
    return m.group(0).lower() if m else name.lower()


def infer_param_size_b(model_id: str) -> float | None:
    """이름의 nB 표기 → 파라미터 규모(B). MoE(8x7B)는 expert 크기 기준."""
    name = model_id.split("/")[-1]
    m = _PARAM_RE.search(name)
    return float(m.group(1)) if m else None


def load_catalog(profile: str = "pilot") -> list[dict]:
    """profile tier 이하 모델 목록 (중복 model_id 는 최저 tier 유지 — 스크립트 dedup 규칙 동일)."""
    if profile not in TIER_RANK:
        raise ValueError(f"invalid profile: {profile}")
    max_rank = TIER_RANK[profile]
    seen: set[str] = set()
    models = []
    for line in _RAW.strip().splitlines():
        tier, model_id, role, notes = line.split("|", 3)
        if TIER_RANK[tier] > max_rank or model_id in seen:
            continue
        seen.add(model_id)
        models.append({
            "model_id": model_id, "tier": tier, "role": role, "notes": notes,
            "family": infer_family(model_id), "param_size_b": infer_param_size_b(model_id),
        })
    return models
