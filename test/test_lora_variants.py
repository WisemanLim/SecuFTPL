"""E16 학습 고도화 테스트 (F19 — lora_variant 토글·mlx-lm LoRA 플랜, impl/48th)."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.db import Base, get_db
from app.main import app


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


def _job(client):
    client.post("/api/v1/models/seed", json={"profile": "pilot"})
    client.post("/api/v1/models/Qwen/Qwen3-14B/pin", json={"revision": "abc1234def"})
    for i in range(500):
        client.post("/api/v1/records/ingest", json={"records": [{
            "messages": [{"role": "user", "content": f"경보 {i}: 서로 다른 내용 {i}"},
                         {"role": "assistant", "content": f"분석 {i}"}],
            "metadata": {"record_id": f"r-lv{i}", "source_uri": "test://fixture",
                         "source_hash_sha256": "f" * 64, "source_type": "manual",
                         "task_type": "alert_triage", "dataset_version": "lv-v1"}}]})
        client.post(f"/api/v1/records/r-lv{i}/review", json={"action": "approve", "reviewer": "t"})
    res = client.post("/api/v1/tuning/jobs",
                      json={"model_id": "Qwen/Qwen3-14B", "dataset_version": "lv-v1"}).json()
    return res["job_id"]


def test_plan_lora_variants(client):
    job_id = _job(client)
    base = client.get(f"/api/v1/tuning/jobs/{job_id}/plan").json()
    assert "lora_variant: lora" in base["plan"] and "use_rslora" not in base["plan"]
    rs = client.get(f"/api/v1/tuning/jobs/{job_id}/plan", params={"lora_variant": "rslora"}).json()
    assert "use_rslora: true" in rs["plan"]
    do = client.get(f"/api/v1/tuning/jobs/{job_id}/plan", params={"lora_variant": "dora"}).json()
    assert "use_dora: true" in do["plan"]
    assert client.get(f"/api/v1/tuning/jobs/{job_id}/plan",
                      params={"lora_variant": "nope"}).status_code == 422


def test_mlx_train_plan(client):
    job_id = _job(client)
    plan = client.get(f"/api/v1/tuning/jobs/{job_id}/train-plan/mlx").json()
    assert plan["backend"] == "mlx-lm"
    assert "mlx_lm.lora" in plan["command"] and "--train" in plan["command"]
    assert "Qwen/Qwen3-14B" in plan["command"]
    assert isinstance(plan["available"], bool)
