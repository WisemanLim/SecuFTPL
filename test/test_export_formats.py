"""dpo-pairs·eval-set export 테스트 (PRD §7.2 F6 잔여)."""
from app.services.formats import convert, export_dpo_pairs, to_eval_set


def _rec(rid, answer, score=None, scale="binary"):
    meta = {"record_id": rid, "dataset_version": "v0.1.0"}
    if score is not None:
        meta["satisfaction"] = {"scale": scale, "score": score}
    return {"messages": [{"role": "user", "content": "경보 분석"},
                         {"role": "assistant", "content": answer}],
            "metadata": meta}


def test_eval_set_export():
    out = to_eval_set(_rec("r-1", "정답"))
    assert out["expected"] == "정답" and out["prompt"][-1]["role"] == "user"
    via_convert = convert([_rec("r-1", "정답")], "canonical", "eval-set")
    assert via_convert[0] == out


def test_dpo_pairs_binary():
    records = [_rec("r-up", "좋은 답", "up"), _rec("r-down", "나쁜 답", "down"),
               _rec("r-none", "무평가 답")]
    pairs = export_dpo_pairs(records)
    assert len(pairs) == 1
    assert pairs[0]["chosen"] == "좋은 답" and pairs[0]["rejected"] == "나쁜 답"
    assert pairs[0]["chosen_record_id"] == "r-up"


def test_dpo_pairs_likert5_and_neutral_excluded():
    records = [_rec("r-5", "훌륭", 5, "likert5"), _rec("r-3", "보통", 3, "likert5"),
               _rec("r-1", "미흡", 1, "likert5")]
    pairs = export_dpo_pairs(records)
    assert len(pairs) == 1 and pairs[0]["chosen"] == "훌륭" and pairs[0]["rejected"] == "미흡"


def test_dpo_pairs_different_prompts_not_paired():
    a = _rec("r-up", "답", "up")
    b = _rec("r-down", "답", "down")
    b["messages"][0]["content"] = "다른 질문"
    assert export_dpo_pairs([a, b]) == []


def test_convert_dpo_target():
    out = convert([_rec("r-up", "A", "up"), _rec("r-down", "B", "down")],
                  "canonical", "dpo-pairs")
    assert out[0]["prompt"] == "경보 분석"
