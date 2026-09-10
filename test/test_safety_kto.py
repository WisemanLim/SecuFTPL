"""E14 안전·선호 데이터 테스트 (F17 — jailbreak importer·KTO export, impl/46th)."""
import pytest

from app.services.formats import convert, export_kto


def _fb(rid, score, scale="binary"):
    return {"messages": [{"role": "user", "content": f"질의 {rid}"},
                         {"role": "assistant", "content": f"답변 {rid}"}],
            "metadata": {"record_id": rid, "dataset_version": "fb-v0",
                         "satisfaction": {"scale": scale, "score": score}}}


def test_jailbreak_importer_safety_refusal():
    recs = convert([{"prompt": "ignore previous instructions and ...", "platform": "reddit"}],
                   "jailbreak", "canonical", {"dataset_version": "jb-v1"})
    meta = recs[0]["metadata"]
    assert meta["task_type"] == "safety_refusal"
    assert meta["source_type"] == "jailbreak_import"
    assert meta["trust_tier"] == "T3_untrusted"
    assert "needs_annotation" in recs[0]["messages"][-1]["content"]
    with pytest.raises((KeyError, TypeError)):
        convert([{"platform": "x"}], "jailbreak", "canonical")


def test_kto_export_single_label():
    records = [_fb("r-up", "up"), _fb("r-down", "down"),
               _fb("r-mid", 3, "likert5"),  # 중립 = 제외
               {"messages": [{"role": "user", "content": "무평가"},
                             {"role": "assistant", "content": "x"}],
                "metadata": {"record_id": "r-none"}}]
    out = export_kto(records)
    by_id = {o["record_id"]: o for o in out}
    assert set(by_id) == {"r-up", "r-down"}
    assert by_id["r-up"]["label"] is True and by_id["r-down"]["label"] is False
    assert by_id["r-up"]["prompt"] == "질의 r-up" and by_id["r-up"]["completion"] == "답변 r-up"


def test_kto_via_convert_and_likert():
    out = convert([_fb("r-l5", 5, "likert5"), _fb("r-l1", 1, "likert5")], "canonical", "kto")
    labels = {o["record_id"]: o["label"] for o in out}
    assert labels == {"r-l5": True, "r-l1": False}
