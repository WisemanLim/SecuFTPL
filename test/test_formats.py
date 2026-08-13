"""포맷 어댑터 테스트 (PRD §7.2 F6 — canonical ↔ alpaca/sharegpt/openai-chat)."""
import pytest

from app.services.formats import convert

ALPACA = {"instruction": "경보 분석", "input": "alert: ...", "output": "결과", "system": "SOC 보조자"}
SHAREGPT = {"conversations": [
    {"from": "system", "value": "SOC 보조자"},
    {"from": "human", "value": "경보 분석"},
    {"from": "gpt", "value": "결과"},
]}
META = {"record_id": "r-1", "dataset_version": "v0.1.0"}


def test_alpaca_roundtrip():
    canonical = convert([ALPACA], "alpaca", "canonical", META)
    assert canonical[0]["messages"][-1] == {"role": "assistant", "content": "결과"}
    assert canonical[0]["messages"][1]["content"] == "경보 분석\n\nalert: ..."
    assert canonical[0]["metadata"]["record_id"] == "r-1"
    back = convert(canonical, "canonical", "alpaca")
    assert back[0]["output"] == "결과" and back[0]["system"] == "SOC 보조자"


def test_sharegpt_roundtrip():
    canonical = convert([SHAREGPT], "sharegpt", "canonical", META)
    roles = [m["role"] for m in canonical[0]["messages"]]
    assert roles == ["system", "user", "assistant"]
    back = convert(canonical, "canonical", "sharegpt")
    assert back[0] == SHAREGPT


def test_cross_format_alpaca_to_openai_chat():
    out = convert([ALPACA], "alpaca", "openai-chat", META)
    assert out[0]["messages"][0]["role"] == "system"
    assert "metadata" not in out[0]


def test_unsupported_format_raises():
    with pytest.raises(ValueError, match="unsupported source"):
        convert([{}], "csv", "canonical")
    with pytest.raises(ValueError, match="unsupported target"):
        convert([ALPACA], "alpaca", "parquet")
