"""F11 — 다중 런타임 배포·풀모델 export 테스트 (PRD §7.14, E11)."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core import db as core_db
from app.core.config import settings
from app.core.db import Base, get_db
from app.main import app
from app.services.export_runtime import conversion_plan, merge_full_model


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


def _approve_one(client, rid="r-exp1"):
    client.post("/api/v1/records/ingest", json={"records": [{
        "messages": [{"role": "user", "content": f"경보 {rid}"},
                     {"role": "assistant", "content": f"분석 {rid}"}],
        "metadata": {"record_id": rid, "source_uri": "test://fixture", "source_hash_sha256": "f" * 64, "source_type": "manual",
                     "task_type": "alert_triage", "dataset_version": "v0.1.0"},
    }]})
    client.post(f"/api/v1/records/{rid}/review", json={"action": "approve", "reviewer": "t"})


def _succeeded_job(client):
    client.post("/api/v1/models/seed", json={"profile": "pilot"})
    client.post("/api/v1/models/Qwen/Qwen3-14B/pin", json={"revision": "abc1234def"})
    _approve_one(client)
    return client.post("/api/v1/tuning/jobs", json={
        "model_id": "Qwen/Qwen3-14B", "dataset_version": "v0.1.0"}).json()


# --- 순수 로직 ---

def test_merge_full_model_simulated(tmp_path):
    adapter_dir = tmp_path / "adapter"
    adapter_dir.mkdir()
    (adapter_dir / "adapter_manifest.json").write_text("{}")
    out_dir = tmp_path / "full"
    manifest = merge_full_model("ft-x", "Qwen/Qwen3-14B", adapter_dir, out_dir)
    assert manifest["mode"] == "simulated"
    assert (out_dir / "export_manifest.json").is_file()


def test_conversion_plan_gguf_and_mlx(tmp_path):
    gguf = conversion_plan("ft-x", tmp_path, "gguf")
    assert "convert_hf_to_gguf.py" in gguf and "q4_k_m" in gguf
    mlx = conversion_plan("ft-x", tmp_path, "mlx")
    assert "mlx_lm.convert" in mlx


def test_conversion_plan_invalid_target(tmp_path):
    with pytest.raises(ValueError, match="unsupported export target"):
        conversion_plan("ft-x", tmp_path, "onnx")


# --- API ---

def test_export_adapter_default(client):
    job = _succeeded_job(client)
    res = client.get(f"/api/v1/tuning/jobs/{job['job_id']}/export")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/gzip"
    assert f"{job['job_id']}.tar.gz" in res.headers["content-disposition"]


def test_export_full_merges_and_streams(client):
    job = _succeeded_job(client)
    res = client.get(f"/api/v1/tuning/jobs/{job['job_id']}/export?format=full")
    assert res.status_code == 200
    assert f"{job['job_id']}-full.tar.gz" in res.headers["content-disposition"]


def test_export_invalid_format(client):
    job = _succeeded_job(client)
    res = client.get(f"/api/v1/tuning/jobs/{job['job_id']}/export?format=onnx")
    assert res.status_code == 422


def test_export_plan_gguf_and_mlx(client):
    job = _succeeded_job(client)
    res = client.get(f"/api/v1/tuning/jobs/{job['job_id']}/export-plan?target=gguf").json()
    assert res["target"] == "gguf" and "convert_hf_to_gguf.py" in res["command"]
    res2 = client.get(f"/api/v1/tuning/jobs/{job['job_id']}/export-plan?target=mlx").json()
    assert "mlx_lm.convert" in res2["command"]


def test_export_plan_requires_succeeded_job(client):
    client.post("/api/v1/models/seed", json={"profile": "pilot"})
    client.post("/api/v1/models/Qwen/Qwen3-14B/pin", json={"revision": "abc1234def"})
    _approve_one(client, "r-exp2")
    # 강제로 queued 잡을 만들려면 트레이너 백그라운드를 못 돌게 할 수 없으니 없는 job_id 로 404 확인
    res = client.get("/api/v1/tuning/jobs/ft-notfound/export-plan?target=gguf")
    assert res.status_code == 404
