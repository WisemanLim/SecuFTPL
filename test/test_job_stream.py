"""잡 진행 실시간 스트리밍(WebSocket) 테스트 — 폴링(/events) 대안 (PRD F9 §7.12)."""
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


def _succeeded_job(client):
    client.post("/api/v1/models/seed", json={"profile": "pilot"})
    client.post("/api/v1/models/Qwen/Qwen3-14B/pin", json={"revision": "abc1234def"})
    client.post("/api/v1/records/ingest", json={"records": [{
        "messages": [{"role": "user", "content": "경보 r-ws1"},
                     {"role": "assistant", "content": "분석 r-ws1"}],
        "metadata": {"record_id": "r-ws1", "source_type": "manual",
                     "task_type": "alert_triage", "dataset_version": "v0.1.0"},
    }]})
    client.post("/api/v1/records/r-ws1/review", json={"action": "approve", "reviewer": "t"})
    return client.post("/api/v1/tuning/jobs", json={
        "model_id": "Qwen/Qwen3-14B", "dataset_version": "v0.1.0"}).json()


def test_stream_finished_job_sends_final_snapshot_and_closes(client):
    job = _succeeded_job(client)  # TestClient 가 BackgroundTasks 를 동기 실행 → 연결 시점엔 이미 succeeded
    with client.websocket_connect(f"/api/v1/tuning/jobs/{job['job_id']}/stream") as ws:
        msg = ws.receive_json()
        assert msg["job_id"] == job["job_id"]
        assert msg["status"] == "succeeded"
        assert msg["progress_pct"] == 100.0
        assert isinstance(msg["new_events"], list) and len(msg["new_events"]) > 0


def test_stream_unknown_job_sends_error(client):
    with client.websocket_connect("/api/v1/tuning/jobs/ft-notfound/stream") as ws:
        msg = ws.receive_json()
        assert "error" in msg and "ft-notfound" in msg["error"]
