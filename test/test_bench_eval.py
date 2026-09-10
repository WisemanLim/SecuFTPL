"""E13 보안 벤치·평가 연동 테스트 (F16 — CTIBench importer·값 정확도·lm-eval YAML·카탈로그, impl/45th)."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.db import Base, get_db
from app.main import app
from app.services.catalog import load_catalog
from app.services.evaluate import evaluate_predictions, value_accuracy
from app.services.formats import convert


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, autoflush=False)

    def override_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_ctibench_importer_with_options():
    items = [{"Question": "Which ATT&CK technique?", "Option A": "T1059", "Option B": "T1003",
              "GT": "A"}]
    recs = convert(items, "ctibench", "canonical", {"dataset_version": "ctibench-v1"})
    assert recs[0]["messages"][0]["content"].startswith("Which ATT&CK technique?")
    assert "A) T1059" in recs[0]["messages"][0]["content"]
    assert recs[0]["messages"][-1]["content"] == "A"
    meta = recs[0]["metadata"]
    assert meta["task_type"] == "cti_extraction" and meta["source_type"] == "benchmark_import"


def test_ctibench_importer_requires_fields():
    with pytest.raises((KeyError, TypeError)):
        convert([{"Question": "no answer"}], "ctibench", "canonical")


def test_value_accuracy_two_axis():
    # 스키마는 유효(JSON dict)하지만 값이 절반만 맞는 케이스 — json_valid 와 분리 측정
    rows = [{"expected": {"severity": "high", "attack_ids": ["T1059"]},
             "prediction": {"severity": "low", "attack_ids": ["T1059"]}}]
    report = evaluate_predictions(rows)
    assert report["json_valid_rate"] == 1.0
    assert report["value_accuracy"] == 0.5
    assert value_accuracy({}, {}) == 1.0
    assert value_accuracy({"a": [2, 1]}, {"a": [1, 2]}) == 1.0  # 리스트 순서 무시


def test_catalog_includes_survey_security_models():
    ids = {m["model_id"] for m in load_catalog("core")}
    assert "fdtn-ai/Foundation-Sec-8B-Instruct" in ids
    assert "trend-cybertron/Llama-Primus-Base" in ids
    assert "segolilylabs/Lily-Cybersecurity-7B-v0.2" in ids


def test_lmeval_task_yaml_export(client):
    rec = {"messages": [{"role": "user", "content": "경보 분석"},
                        {"role": "assistant", "content": "분석 결과"}],
           "metadata": {"record_id": "r-lm1", "source_uri": "test://fixture",
                        "source_hash_sha256": "f" * 64, "source_type": "manual",
                        "task_type": "alert_triage", "dataset_version": "v0.1.0"}}
    client.post("/api/v1/records/ingest", json={"records": [rec]})
    client.post("/api/v1/records/r-lm1/review", json={"action": "approve", "reviewer": "t"})
    res = client.get("/api/v1/datasets/export/lmeval-task", params={"dataset_version": "v0.1.0"})
    assert res.status_code == 200
    body = res.text
    assert "task: secuftpl_v0_1_0" in body and "data_files: " in body
    assert client.get("/api/v1/datasets/export/lmeval-task",
                      params={"dataset_version": "nope"}).status_code == 404
