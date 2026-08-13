"""F9 — 튜닝 시작 최소 데이터셋 게이트 + 리소스 세부설정/모니터링 (PRD §7.5·§7.12)."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core import db as core_db
from app.core.config import settings
from app.core.db import Base, get_db
from app.main import app


@pytest.fixture()
def client(monkeypatch, tmp_path):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, autoflush=False)
    from app.services import trainer

    monkeypatch.setattr(core_db, "engine", engine)
    monkeypatch.setattr(core_db, "SessionLocal", TestSession)
    monkeypatch.setattr(trainer, "ADAPTER_ROOT", tmp_path / "adapters")
    monkeypatch.setattr(trainer.time, "sleep", lambda s: None)

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


def _approve_n(client, n):
    for i in range(n):
        rid = f"r-gate{i}"
        client.post("/api/v1/records/ingest", json={"records": [{
            "messages": [{"role": "user", "content": f"경보 {rid}"},
                         {"role": "assistant", "content": f"분석 {rid}"}],
            "metadata": {"record_id": rid, "source_type": "manual",
                         "task_type": "alert_triage", "dataset_version": "v0.1.0"},
        }]})
        client.post(f"/api/v1/records/{rid}/review", json={"action": "approve", "reviewer": "t"})


def test_job_blocked_below_dataset_min_records(client):
    assert settings.dataset_min_records == 500  # 기본값 확인(테스트에서 낮추지 않음)
    client.post("/api/v1/models/seed", json={"profile": "pilot"})
    client.post("/api/v1/models/Qwen/Qwen3-14B/pin", json={"revision": "abc1234def"})
    _approve_n(client, 3)  # 500건 미달
    res = client.post("/api/v1/tuning/jobs",
                      json={"model_id": "Qwen/Qwen3-14B", "dataset_version": "v0.1.0"})
    assert res.status_code == 422
    assert "500" in res.json()["detail"]


def test_job_resource_limits_and_monitoring(client, monkeypatch):
    monkeypatch.setattr(settings, "dataset_min_records", 1)
    client.post("/api/v1/models/seed", json={"profile": "pilot"})
    client.post("/api/v1/models/Qwen/Qwen3-14B/pin", json={"revision": "abc1234def"})
    _approve_n(client, 1)
    job = client.post("/api/v1/tuning/jobs", json={
        "model_id": "Qwen/Qwen3-14B", "dataset_version": "v0.1.0",
        "max_gpu": 2, "max_vram_gb": 48,
    }).json()
    assert job["max_gpu"] == 2 and job["max_vram_gb"] == 48

    res = client.get(f"/api/v1/tuning/jobs/{job['job_id']}/resources").json()
    assert res["limits"] == {"max_gpu": 2, "max_vram_gb": 48}
    assert res["gpu_mode"] in ("real", "simulated")
    assert len(res["gpu_devices"]) == 2
    assert 0 <= res["cpu_pct"] <= 100
    assert 0 <= res["mem_used_pct"] <= 100


def test_job_default_resource_limits_from_settings(client, monkeypatch):
    monkeypatch.setattr(settings, "dataset_min_records", 1)
    monkeypatch.setattr(settings, "job_max_gpu", 1)
    monkeypatch.setattr(settings, "job_max_vram_gb", 24)
    client.post("/api/v1/models/seed", json={"profile": "pilot"})
    client.post("/api/v1/models/Qwen/Qwen3-14B/pin", json={"revision": "abc1234def"})
    _approve_n(client, 1)
    job = client.post("/api/v1/tuning/jobs", json={
        "model_id": "Qwen/Qwen3-14B", "dataset_version": "v0.1.0"}).json()
    assert job["max_gpu"] == 1 and job["max_vram_gb"] == 24
