"""F9 — 리소스 상한 초과 시 실제 큐잉 (PRD §7.12, TOTAL_GPU_CAPACITY)."""
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
    monkeypatch.setattr(settings, "dataset_min_records", 1)

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


def _approve_one(client, rid="r-q1"):
    client.post("/api/v1/records/ingest", json={"records": [{
        "messages": [{"role": "user", "content": f"경보 {rid}"},
                     {"role": "assistant", "content": f"분석 {rid}"}],
        "metadata": {"record_id": rid, "source_uri": "test://fixture", "source_hash_sha256": "f" * 64, "source_type": "manual",
                     "task_type": "alert_triage", "dataset_version": "v0.1.0"},
    }]})
    client.post(f"/api/v1/records/{rid}/review", json={"action": "approve", "reviewer": "t"})


def _setup_model(client):
    client.post("/api/v1/models/seed", json={"profile": "pilot"})
    client.post("/api/v1/models/Qwen/Qwen3-14B/pin", json={"revision": "abc1234def"})


def test_job_exceeding_total_capacity_stays_queued(client, monkeypatch):
    monkeypatch.setattr(settings, "total_gpu_capacity", 1)
    _setup_model(client)
    _approve_one(client)
    job = client.post("/api/v1/tuning/jobs", json={
        "model_id": "Qwen/Qwen3-14B", "dataset_version": "v0.1.0", "max_gpu": 2,
    }).json()
    jobs = client.get("/api/v1/tuning/jobs").json()["jobs"]
    row = next(j for j in jobs if j["job_id"] == job["job_id"])
    assert row["status"] == "queued"  # 2 > 상한 1 → 큐잉, 학습 시작 안 됨
    assert row["progress_pct"] == 0.0


def test_job_within_capacity_dispatches_immediately(client, monkeypatch):
    monkeypatch.setattr(settings, "total_gpu_capacity", 2)
    _setup_model(client)
    _approve_one(client)
    job = client.post("/api/v1/tuning/jobs", json={
        "model_id": "Qwen/Qwen3-14B", "dataset_version": "v0.1.0", "max_gpu": 1,
    }).json()
    jobs = client.get("/api/v1/tuning/jobs").json()["jobs"]
    row = next(j for j in jobs if j["job_id"] == job["job_id"])
    assert row["status"] == "succeeded"


def test_queued_job_starts_after_capacity_raised_via_retry(client, monkeypatch):
    monkeypatch.setattr(settings, "total_gpu_capacity", 1)
    _setup_model(client)
    _approve_one(client)
    job = client.post("/api/v1/tuning/jobs", json={
        "model_id": "Qwen/Qwen3-14B", "dataset_version": "v0.1.0", "max_gpu": 2,
    }).json()
    jid = job["job_id"]
    assert next(j for j in client.get("/api/v1/tuning/jobs").json()["jobs"]
               if j["job_id"] == jid)["status"] == "queued"

    monkeypatch.setattr(settings, "total_gpu_capacity", 2)  # 상한 상향
    client.post(f"/api/v1/tuning/jobs/{jid}/retry")
    row = next(j for j in client.get("/api/v1/tuning/jobs").json()["jobs"] if j["job_id"] == jid)
    assert row["status"] == "succeeded"


def test_batch_created_job_is_actually_dispatched(client):
    """배치가 만든 잡이 이전엔 워커 미투입으로 queued 에 머물렀던 결함 수정 확인(F9 큐잉 도입과 함께)."""
    _setup_model(client)
    _approve_one(client)
    run = client.post("/api/v1/batch/run", json={"mode": "schedule"}).json()
    assert run["status"] == "jobs_created"
    jid = run["jobs"][0]
    row = next(j for j in client.get("/api/v1/tuning/jobs").json()["jobs"] if j["job_id"] == jid)
    assert row["status"] == "succeeded"
