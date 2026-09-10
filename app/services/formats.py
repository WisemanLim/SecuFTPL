"""secuftpl — 데이터셋 포맷 변환 어댑터 (PRD §7.2 F6).

canonical(sft-messages) ↔ alpaca / sharegpt / openai-chat.
export 전용: eval-set(레코드별), dpo-pairs(만족도 up/down 쌍 — 동일 prompt 그룹).
"""
from collections.abc import Callable
from typing import Any

ImportFn = Callable[[dict, dict], dict]
ExportFn = Callable[[dict], dict]

_SHAREGPT_TO_ROLE = {"system": "system", "human": "user", "gpt": "assistant"}
_ROLE_TO_SHAREGPT = {v: k for k, v in _SHAREGPT_TO_ROLE.items()}


def _base_metadata(defaults: dict) -> dict:
    meta = {
        "record_id": "",
        "source_type": "import",
        "task_type": "generic",
        "dataset_version": "unversioned",
    }
    meta.update(defaults)
    return meta


def from_alpaca(item: dict, meta_defaults: dict) -> dict:
    user = item["instruction"]
    if item.get("input"):
        user = f"{user}\n\n{item['input']}"
    messages = []
    if item.get("system"):
        messages.append({"role": "system", "content": item["system"]})
    messages += [
        {"role": "user", "content": user},
        {"role": "assistant", "content": item["output"]},
    ]
    return {"messages": messages, "metadata": _base_metadata(meta_defaults)}


def to_alpaca(record: dict) -> dict:
    msgs = record["messages"]
    system = next((m["content"] for m in msgs if m["role"] == "system"), None)
    user = next(m["content"] for m in msgs if m["role"] == "user")
    out = {"instruction": user, "input": "", "output": msgs[-1]["content"]}
    if system:
        out["system"] = system
    return out


def from_sharegpt(item: dict, meta_defaults: dict) -> dict:
    messages = [
        {"role": _SHAREGPT_TO_ROLE[c["from"]], "content": c["value"]}
        for c in item["conversations"]
    ]
    return {"messages": messages, "metadata": _base_metadata(meta_defaults)}


def to_sharegpt(record: dict) -> dict:
    return {
        "conversations": [
            {"from": _ROLE_TO_SHAREGPT[m["role"]], "value": m["content"]}
            for m in record["messages"]
        ]
    }


def from_openai_chat(item: dict, meta_defaults: dict) -> dict:
    return {"messages": list(item["messages"]), "metadata": _base_metadata(meta_defaults)}


def to_openai_chat(record: dict) -> dict:
    return {"messages": [{"role": m["role"], "content": m["content"]} for m in record["messages"]]}


def from_ctibench(item: dict, meta_defaults: dict) -> dict:
    """CTIBench 계열 벤치마크 행 → canonical (PRD F16, Survey §2.3).
    지원 키(대소문자 무관): question/prompt + answer/gt, 선택지 option a~d."""
    low = {k.lower(): v for k, v in item.items()}
    question = low.get("question") or low.get("prompt")
    answer = low.get("answer") or low.get("gt")
    if not question or answer is None:
        raise KeyError("ctibench item requires question/prompt and answer/gt")
    options = [f"{k[-1].upper()}) {v}" for k, v in sorted(low.items())
               if k.startswith("option ") and v]
    user = question if not options else question + "\n\n" + "\n".join(options)
    meta = _base_metadata({"task_type": "cti_extraction", "source_type": "benchmark_import",
                           **meta_defaults})
    return {"messages": [{"role": "user", "content": user},
                         {"role": "assistant", "content": str(answer)}],
            "metadata": meta}


_REFUSAL_NEEDS_ANNOTATION = (
    '{"status": "needs_annotation", '
    '"note": "safety_refusal 레코드 — 검수 단계에서 범위 제한+방어적 대안 거부 응답 작성 (PRD §7.3)"}'
)


def from_jailbreak(item: dict, meta_defaults: dict) -> dict:
    """jailbreak 프롬프트 행 → safety_refusal 주석대기 canonical (PRD F17, Survey jailbreak_llms).
    지원 키: prompt(필수), platform/source(출처 참고). 정답(거부 응답)은 검수 단계에서 작성."""
    prompt = item.get("prompt")
    if not prompt:
        raise KeyError("jailbreak item requires prompt")
    meta = _base_metadata({"task_type": "safety_refusal", "source_type": "jailbreak_import",
                           "trust_tier": "T3_untrusted", **meta_defaults})
    return {"messages": [{"role": "user", "content": prompt},
                         {"role": "assistant", "content": _REFUSAL_NEEDS_ANNOTATION}],
            "metadata": meta}


IMPORTERS: dict[str, ImportFn] = {
    "alpaca": from_alpaca,
    "sharegpt": from_sharegpt,
    "openai-chat": from_openai_chat,
    "ctibench": from_ctibench,
    "jailbreak": from_jailbreak,
}
def to_eval_set(record: dict) -> dict:
    """평가셋 포맷: prompt(마지막 assistant 제외) + expected(정답). 증강본 제외는 호출측 책임(PRD §7.4)."""
    return {
        "record_id": record["metadata"]["record_id"],
        "prompt": [
            {"role": m["role"], "content": m["content"]} for m in record["messages"][:-1]
        ],
        "expected": record["messages"][-1]["content"],
    }


EXPORTERS: dict[str, ExportFn] = {
    "alpaca": to_alpaca,
    "sharegpt": to_sharegpt,
    "openai-chat": to_openai_chat,
    "eval-set": to_eval_set,
}


def _prompt_key(record: dict) -> str:
    return "\n".join(m["content"] for m in record["messages"][:-1])


def _dpo_bucket(record: dict) -> str | None:
    """만족도 → chosen/rejected 버킷 (binary: up/down, likert5: 4~5/1~2, 3=제외)."""
    sat = (record.get("metadata") or {}).get("satisfaction")
    if not sat:
        return None
    score = sat.get("score")
    if score == "up" or (isinstance(score, int) and score >= 4):
        return "chosen"
    if score == "down" or (isinstance(score, int) and score <= 2):
        return "rejected"
    return None


def export_dpo_pairs(records: list[dict]) -> list[dict]:
    """만족도 기반 DPO 선호쌍: 동일 prompt 의 up(chosen) × down(rejected) 조합 (PRD §7.9)."""
    groups: dict[str, dict[str, list[dict]]] = {}
    for r in records:
        bucket = _dpo_bucket(r)
        if bucket is None:
            continue
        groups.setdefault(_prompt_key(r), {"chosen": [], "rejected": []})[bucket].append(r)
    pairs = []
    for key, g in groups.items():
        for chosen in g["chosen"]:
            for rejected in g["rejected"]:
                pairs.append({
                    "prompt": key,
                    "chosen": chosen["messages"][-1]["content"],
                    "rejected": rejected["messages"][-1]["content"],
                    "chosen_record_id": chosen["metadata"]["record_id"],
                    "rejected_record_id": rejected["metadata"]["record_id"],
                })
    return pairs


def export_kto(records: list[dict]) -> list[dict]:
    """만족도 → KTO 단건 라벨 포맷 (PRD F17, Survey §2.1 KTO — 쌍 불필요 선호학습).
    up/likert≥4 = true, down/likert≤2 = false, 중립(3)·무평가 = 제외."""
    out = []
    for r in records:
        bucket = _dpo_bucket(r)
        if bucket is None:
            continue
        out.append({
            "prompt": _prompt_key(r),
            "completion": r["messages"][-1]["content"],
            "label": bucket == "chosen",
            "record_id": r["metadata"]["record_id"],
        })
    return out


def convert(items: list[dict], source: str, target: str, meta_defaults: dict | None = None) -> list[dict[str, Any]]:
    """source 포맷 → canonical → target 포맷. source/target 중 하나는 'canonical' 가능."""
    meta_defaults = meta_defaults or {}
    if source == "canonical":
        canonical = items
    elif source in IMPORTERS:
        canonical = [IMPORTERS[source](i, meta_defaults) for i in items]
    else:
        raise ValueError(f"unsupported source format: {source}")
    if target == "canonical":
        return canonical
    if target == "dpo-pairs":  # 리스트 단위 변환 (레코드별 아님)
        return export_dpo_pairs(canonical)
    if target == "kto":  # 리스트 단위 — 만족도 없는 레코드 제외
        return export_kto(canonical)
    if target in EXPORTERS:
        return [EXPORTERS[target](r) for r in canonical]
    raise ValueError(f"unsupported target format: {target}")
