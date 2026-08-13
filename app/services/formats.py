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


IMPORTERS: dict[str, ImportFn] = {
    "alpaca": from_alpaca,
    "sharegpt": from_sharegpt,
    "openai-chat": from_openai_chat,
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
    if target in EXPORTERS:
        return [EXPORTERS[target](r) for r in canonical]
    raise ValueError(f"unsupported target format: {target}")
