"""F10 — RAG 기반 추가학습·모델 업그레이드 테스트 (PRD §7.13, E10)."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core import db as core_db
from app.core.config import settings
from app.core.db import Base, get_db
from app.main import app
from app.services.rag_synth import chunk_text, synthesize_records


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


# --- 순수 합성 로직 ---

def test_chunk_text_splits_by_size():
    chunks = chunk_text("가" * 1900, chunk_size=800)
    assert len(chunks) == 3
    assert all(len(c) <= 800 for c in chunks)


def test_chunk_text_empty():
    assert chunk_text("   ") == []


def test_synthesize_records_deterministic_fallback():
    recs = synthesize_records(["원인 문장. 해결 문장."], "alert_triage", "v0.1.0", "doc-A")
    assert len(recs) == 1
    rec = recs[0]
    assert rec["metadata"]["source_type"] == "rag_synthesis"
    assert rec["metadata"]["quality_grade"] == "augmented"
    assert rec["metadata"]["source_uri"] == "doc-A"
    import json
    answer = json.loads(rec["messages"][-1]["content"])
    assert answer["citations"] == ["doc-A"]
    assert answer["cause"] and answer["resolution"]


# --- API: 합성 → 검수 → 업그레이드 잡 ---

def test_synthesize_endpoint_ingests_pending_records(client):
    res = client.post("/api/v1/rag/synthesize", json={
        "documents": [{"title": "threat-report-1", "text": "긴 위협 리포트 본문. " * 50}],
        "task_type": "cti_extraction", "dataset_version": "v0.2.0", "chunk_size": 200,
    }).json()
    assert res["documents"] == 1
    assert res["chunks"] > 0
    assert res["ingest"]["queued"] == res["chunks"]


def test_synthesize_rejects_empty_documents(client):
    res = client.post("/api/v1/rag/synthesize", json={
        "documents": [{"title": "empty", "text": " "}],
    })
    assert res.status_code == 422


def test_upgrade_requires_registered_downloaded_model(client):
    res = client.post("/api/v1/rag/upgrade", json={
        "model_id": "no/model", "dataset_version": "v0.1.0"})
    assert res.status_code == 422


def _approve_via_rag(client, n=1):
    res = client.post("/api/v1/rag/synthesize", json={
        "documents": [{"title": f"doc-{i}", "text": f"원인 설명 {i}. 해결 방안 {i}."} for i in range(n)],
        "dataset_version": "v0.1.0",
    }).json()
    for item in res["ingest"]["results"]:
        if item["status"] == "queued":
            client.post(f"/api/v1/records/{item['record_id']}/review",
                       json={"action": "approve", "reviewer": "t"})


def test_upgrade_creates_continual_job_and_appears_on_leaderboard(client):
    client.post("/api/v1/models/seed", json={"profile": "pilot"})
    client.post("/api/v1/models/Qwen/Qwen3-14B/pin", json={"revision": "abc1234def"})
    _approve_via_rag(client, 1)
    base_job = client.post("/api/v1/tuning/jobs", json={
        "model_id": "Qwen/Qwen3-14B", "dataset_version": "v0.1.0"}).json()

    up = client.post("/api/v1/rag/upgrade", json={
        "model_id": "Qwen/Qwen3-14B", "dataset_version": "v0.1.0",
        "continual_from_job_id": base_job["job_id"],
    }).json()
    assert up["continual_from_job_id"] == base_job["job_id"]
    lb = client.get("/api/v1/tuning/leaderboard?dataset_version=v0.1.0").json()
    job_ids = {item["job_id"] for item in lb["items"]}
    assert base_job["job_id"] in job_ids
    assert up["job_id"] in job_ids


def test_upgrade_rejects_continual_from_non_succeeded_job(client, monkeypatch):
    monkeypatch.setattr(settings, "dataset_min_records", 1)
    client.post("/api/v1/models/seed", json={"profile": "pilot"})
    client.post("/api/v1/models/Qwen/Qwen3-14B/pin", json={"revision": "abc1234def"})
    res = client.post("/api/v1/rag/upgrade", json={
        "model_id": "Qwen/Qwen3-14B", "dataset_version": "v0.1.0",
        "continual_from_job_id": "ft-does-not-exist",
    })
    assert res.status_code == 422
    assert "continual_from_job_id" in res.json()["detail"]
