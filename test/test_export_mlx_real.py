"""F11 — 실 MLX 변환 실행(mlx-lm, Apple Silicon) 테스트. `uv sync --extra mlx` 설치 시에만 실행."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.db import Base, get_db
from app.main import app
from app.services.export_runtime import _mlx_available, convert_to_mlx

pytestmark = pytest.mark.skipif(not _mlx_available(), reason="mlx-lm not installed")


@pytest.fixture()
def client(monkeypatch, tmp_path):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, autoflush=False)
    from app.core import db as core_db
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
        "messages": [{"role": "user", "content": "경보 r-mlx1"},
                     {"role": "assistant", "content": "분석 r-mlx1"}],
        "metadata": {"record_id": "r-mlx1", "source_type": "manual",
                     "task_type": "alert_triage", "dataset_version": "v0.1.0"},
    }]})
    client.post("/api/v1/records/r-mlx1/review", json={"action": "approve", "reviewer": "t"})
    return client.post("/api/v1/tuning/jobs", json={
        "model_id": "Qwen/Qwen3-14B", "dataset_version": "v0.1.0"}).json()


def test_convert_to_mlx_raises_on_simulated_manifest_only(tmp_path):
    """peft/torch 미설치라 merge_full_model 이 시뮬레이션 매니페스트만 생성 →
    실 HF 가중치가 없어 mlx_lm.convert 가 FileNotFoundError 로 실패해야 함(정직한 실패)."""
    full_dir = tmp_path / "full"
    full_dir.mkdir()
    (full_dir / "export_manifest.json").write_text("{}")
    with pytest.raises(FileNotFoundError):
        convert_to_mlx(full_dir, tmp_path / "mlx_out")


def test_export_mlx_endpoint_422_on_non_hf_full_model(client):
    """실 job 흐름 전체 — 시뮬레이션 merge 산출물로는 변환 실패(422)해야 함(가짜 성공 금지)."""
    job = _succeeded_job(client)
    res = client.post(f"/api/v1/tuning/jobs/{job['job_id']}/export/mlx")
    assert res.status_code == 422
    assert "mlx conversion failed" in res.json()["detail"]


def test_export_mlx_endpoint_requires_succeeded_job(client):
    res = client.post("/api/v1/tuning/jobs/ft-notfound/export/mlx")
    assert res.status_code == 404
