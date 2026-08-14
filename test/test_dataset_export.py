"""F13(데이터셋 export)·F14(출처 필수)·F15(파이프라인 run 추적) 테스트 — PRD §7.15, impl/41st."""
import io
import json
import zipfile

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


def _rec(rid, user="경보를 분석하라", source_uri="test://fixture"):
    return {"messages": [{"role": "user", "content": user},
                         {"role": "assistant", "content": f"분석 결과 {rid}"}],
            "metadata": {"record_id": rid, "source_uri": source_uri,
                         "source_hash_sha256": "f" * 64, "source_type": "manual",
                         "task_type": "alert_triage", "dataset_version": "v0.1.0"}}


def _ingest_and_approve(client, rid, **kw):
    client.post("/api/v1/records/ingest", json={"records": [_rec(rid, **kw)]})
    client.post(f"/api/v1/records/{rid}/review", json={"action": "approve", "reviewer": "t"})


# --- F14 출처 필수화 ---

def test_ingest_rejects_missing_attribution(client):
    rec = _rec("r-noattr")
    del rec["metadata"]["source_uri"]
    del rec["metadata"]["source_hash_sha256"]
    res = client.post("/api/v1/records/ingest", json={"records": [rec]}).json()
    assert res["queued"] == 0
    assert res["results"][0]["status"] == "rejected_attribution"
    assert any("source_uri" in e for e in res["results"][0]["errors"])


def test_upload_channel_auto_stamps_attribution(client):
    line = json.dumps(_upload_rec(), ensure_ascii=False)
    res = client.post("/api/v1/records/upload",
                      files=[("files", ("d.jsonl", line.encode(), "application/jsonl"))]).json()
    assert res["ingest"]["queued"] == 1
    rid = res["ingest"]["results"][0]["record_id"]
    detail = client.get(f"/api/v1/records/{rid}").json()
    meta = detail["payload"]["metadata"]
    assert meta["source_uri"] == "upload://d.jsonl"
    assert len(meta["source_hash_sha256"]) == 64


def _upload_rec():
    # 출처 필드 없는 원본 — 업로드 채널이 자동 스탬핑해야 함
    return {"messages": [{"role": "user", "content": "업로드 경보 분석"},
                         {"role": "assistant", "content": "업로드 분석 결과"}],
            "metadata": {"record_id": "r-up1", "source_type": "file_upload",
                         "task_type": "alert_triage", "dataset_version": "v0.1.0"}}


def test_queue_exposes_source_uri(client):
    client.post("/api/v1/records/ingest", json={"records": [_rec("r-q1")]})
    items = client.get("/api/v1/records/queue").json()["items"]
    assert items[0]["source_uri"] == "test://fixture"
    assert items[0]["license"] == "internal-restricted"


# --- F13 데이터셋 export ---

def test_export_jsonl_approved_only(client):
    _ingest_and_approve(client, "r-e1")
    client.post("/api/v1/records/ingest", json={"records": [_rec("r-e2", user="다른 경보")]})  # pending
    res = client.get("/api/v1/datasets/export")
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("application/x-ndjson")
    lines = [json.loads(x) for x in res.content.decode().splitlines()]
    assert len(lines) == 1 and lines[0]["metadata"]["record_id"] == "r-e1"


def test_export_zip_with_manifest_sources_and_hash(client):
    _ingest_and_approve(client, "r-m1", source_uri="test://a")
    _ingest_and_approve(client, "r-m2", user="두번째 경보", source_uri="test://b")
    res = client.get("/api/v1/datasets/export", params={"with_manifest": "true", "format": "alpaca"})
    assert res.status_code == 200 and res.headers["content-type"] == "application/zip"
    zf = zipfile.ZipFile(io.BytesIO(res.content))
    names = set(zf.namelist())
    assert names == {"dataset.alpaca.jsonl", "manifest.json"}
    manifest = json.loads(zf.read("manifest.json"))
    assert manifest["record_count"] == 2 and manifest["format"] == "alpaca"
    assert set(manifest["sources"]) == {"test://a", "test://b"}
    import hashlib
    assert manifest["file_sha256"] == hashlib.sha256(zf.read("dataset.alpaca.jsonl")).hexdigest()


def test_export_manifest_preview_and_errors(client):
    assert client.get("/api/v1/datasets/export", params={"format": "nope"}).status_code == 422
    assert client.get("/api/v1/datasets/export").status_code == 404  # 레코드 없음
    _ingest_and_approve(client, "r-p1")
    manifest = client.get("/api/v1/datasets/export/manifest").json()
    assert manifest["record_count"] == 1
    assert manifest["distribution"]["task_type"]["alert_triage"] == 1


# --- F15 파이프라인 run 추적 ---

def test_ingest_records_pipeline_run(client):
    rec_ok = _rec("r-r1")
    rec_bad = _rec("r-r2")
    del rec_bad["metadata"]["source_uri"]
    res = client.post("/api/v1/records/ingest", json={"records": [rec_ok, rec_bad]}).json()
    run_id = res["run_id"]
    runs = client.get("/api/v1/datasets/runs").json()
    assert runs["count"] >= 1 and runs["items"][0]["run_id"] == run_id
    detail = client.get(f"/api/v1/datasets/runs/{run_id}").json()
    assert detail["channel"] == "api_ingest"
    assert detail["stats"]["total"] == 2
    assert detail["stats"]["queued"] == 1
    assert detail["stats"]["rejected_attribution"] == 1
    assert detail["stats"]["reason_samples"][0]["index"] == 1
    assert detail["sources"]["test://fixture"]["count"] == 1
    assert detail["sources"]["(missing)"]["count"] == 1


def test_runs_channel_filter_and_404(client):
    client.post("/api/v1/records/ingest", json={"records": [_rec("r-c1")]})
    assert client.get("/api/v1/datasets/runs", params={"channel": "file_upload"}).json()["count"] == 0
    assert client.get("/api/v1/datasets/runs/run-none").status_code == 404
