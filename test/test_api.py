"""데이터셋 API 테스트 (E1 엔드포인트 + 만족도 스키마)."""
import pytest
from fastapi.testclient import TestClient

from app.core.schemas import Satisfaction
from app.main import app

client = TestClient(app)

RECORD = {
    "messages": [
        {"role": "user", "content": "경보 분석하라."},
        {"role": "assistant", "content": "{\"cause\":\"...\"}"},
    ],
    "metadata": {
        "record_id": "r-1",
        "source_type": "assistant_feedback",
        "task_type": "alert_triage",
        "dataset_version": "v0.1.0",
    },
}


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_formats_endpoint():
    body = client.get("/api/v1/datasets/formats").json()
    assert body["canonical"] == "sft-messages"
    assert "alpaca" in body["import"] and "openai-chat" in body["export"]


def test_validate_endpoint():
    res = client.post("/api/v1/datasets/validate", json={"records": [RECORD]})
    assert res.status_code == 200 and res.json()["valid"] == 1


def test_convert_endpoint_and_error():
    res = client.post("/api/v1/datasets/convert", json={
        "items": [{"instruction": "q", "output": "a"}], "source": "alpaca", "target": "canonical",
    })
    assert res.status_code == 200 and res.json()["count"] == 1
    bad = client.post("/api/v1/datasets/convert", json={
        "items": [{"x": 1}], "source": "csv", "target": "canonical",
    })
    assert bad.status_code == 422


def test_satisfaction_binary_and_likert5():
    assert Satisfaction(scale="binary", score="up").score == "up"
    assert Satisfaction(scale="likert5", score=4).score == 4
    with pytest.raises(ValueError):
        Satisfaction(scale="binary", score=3)
    with pytest.raises(ValueError):
        Satisfaction(scale="likert5", score="up")
