"""모델 레지스트리 테스트 (PRD F2, E2 — 카탈로그·유사판정·pin/manifest·download plan)."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.db import Base, get_db
from app.main import app
from app.services.catalog import infer_family, infer_param_size_b, load_catalog


@pytest.fixture()
def client(monkeypatch):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, autoflush=False)
    # 다운로드/학습 백그라운드 워커가 전역 SessionLocal 사용 → 동일 in-memory DB 로 교체
    from app.core import db as core_db
    monkeypatch.setattr(core_db, "engine", engine)
    monkeypatch.setattr(core_db, "SessionLocal", TestSession)
    monkeypatch.setattr(settings, "dataset_min_records", 1)  # 최소 500건 게이트는 별도 시험(F9)

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


# --- 카탈로그 ---

def test_catalog_pilot_matches_script():
    pilot = load_catalog("pilot")
    assert len(pilot) == 12  # 스크립트 pilot 프로파일과 동일
    assert pilot[0]["model_id"] == "Qwen/Qwen3-14B"


def test_catalog_dedup_and_tiers():
    all_models = load_catalog("all")
    ids = [m["model_id"] for m in all_models]
    assert len(ids) == len(set(ids))  # 중복 제거
    assert len(load_catalog("core")) > 12
    with pytest.raises(ValueError):
        load_catalog("mega")


def test_family_and_param_inference():
    assert infer_family("Qwen/Qwen3-14B") == "qwen"
    assert infer_family("meta-llama/Llama-3.1-8B-Instruct") == "llama"
    assert infer_param_size_b("Qwen/Qwen2.5-7B-Instruct") == 7.0
    assert infer_param_size_b("LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct") == 7.8
    assert infer_param_size_b("microsoft/phi-4") is None


# --- API ---

def test_seed_idempotent(client):
    r1 = client.post("/api/v1/models/seed", json={"profile": "pilot"}).json()
    assert r1["added"] == 12
    r2 = client.post("/api/v1/models/seed", json={"profile": "pilot"}).json()
    assert r2["added"] == 0 and r2["skipped"] == 12
    listed = client.get("/api/v1/models?status=registered").json()
    assert listed["count"] == 12


def test_pin_and_manifest(client):
    client.post("/api/v1/models/seed", json={"profile": "pilot"})
    res = client.post("/api/v1/models/Qwen/Qwen3-14B/pin",
                      json={"revision": "abc1234def"}).json()
    assert res["status"] == "pinned"
    man = client.get("/api/v1/models/manifest").json()
    assert man["count"] == 1 and man["models"][0]["revision"] == "abc1234def"
    assert client.post("/api/v1/models/none/exist/pin",
                       json={"revision": "abc1234def"}).status_code == 404


def test_download_status_transition(client, tmp_path, monkeypatch):
    from app.services import model_download
    monkeypatch.setattr(model_download, "MODEL_ROOT", tmp_path / "models")
    monkeypatch.setattr(model_download.time, "sleep", lambda s: None)
    client.post("/api/v1/models/seed", json={"profile": "pilot"})
    mid = "Qwen/Qwen3-14B"
    # registered → download → downloaded (TestClient 가 BackgroundTasks 실행)
    assert client.post(f"/api/v1/models/{mid}/download").json()["status"] == "downloading"
    detail = client.get(f"/api/v1/models/{mid}/detail").json()
    assert detail["status"] == "downloaded" and detail["usable_for_training"] is True
    assert detail["snapshot_manifest"]["mode"] == "simulate"
    # 재다운로드 차단
    assert client.post(f"/api/v1/models/{mid}/download").status_code == 409


def test_training_requires_downloaded_model(client):
    client.post("/api/v1/models/seed", json={"profile": "pilot"})
    client.post("/api/v1/records/ingest", json={"records": [{
        "messages": [{"role": "user", "content": "q"},
                     {"role": "assistant", "content": '{"severity":"high","attack_ids":["T1059.001"]}'}],
        "metadata": {"record_id": "r-dl", "source_type": "manual",
                     "task_type": "alert_triage", "dataset_version": "v0.1.0"}}]})
    client.post("/api/v1/records/r-dl/review", json={"action": "approve", "reviewer": "t"})
    # registered(미다운로드) 모델로 잡 생성 → 422 (다운로드 필요) — 워커 진입 전 차단
    res = client.post("/api/v1/tuning/jobs",
                      json={"model_id": "Qwen/Qwen3-14B", "dataset_version": "v0.1.0"})
    assert res.status_code == 422 and "다운로드" in res.json()["detail"]


def test_download_plan_command(client):
    client.post("/api/v1/models/seed", json={"profile": "pilot"})
    client.post("/api/v1/models/Qwen/Qwen3-14B/pin", json={"revision": "abc1234def"})
    plan = client.get("/api/v1/models/Qwen/Qwen3-14B/download-plan").json()
    cmd = plan["command"]
    assert cmd.startswith("hf download Qwen/Qwen3-14B")
    assert "--revision abc1234def" in cmd and "--exclude '*.gguf'" in cmd


def test_events_scan_similarity(client):
    client.post("/api/v1/models/seed", json={"profile": "pilot"})
    res = client.post("/api/v1/models/events/scan", json={"discovered": [
        {"model_id": "Qwen/Qwen3-15B-Preview"},          # qwen 계열·규모 유사 → candidate
        {"model_id": "unknown-org/TinyNet-0.1B"},         # 비유사 → skip
        {"model_id": "Qwen/Qwen3-14B"},                   # 기등록 → skip
    ]}).json()
    by_id = {r["model_id"]: r for r in res["results"]}
    assert by_id["Qwen/Qwen3-15B-Preview"]["status"] == "candidate"
    assert by_id["Qwen/Qwen3-15B-Preview"]["matched_to"].startswith("Qwen/")
    assert by_id["unknown-org/TinyNet-0.1B"]["status"] == "skipped_not_similar"
    assert by_id["Qwen/Qwen3-14B"]["status"] == "skipped_exists"
    cands = client.get("/api/v1/models?status=candidate").json()
    assert cands["count"] == 1 and cands["models"][0]["source"] == "event"


def test_events_scan_custom_criteria_family_only(client):
    client.post("/api/v1/models/seed", json={"profile": "pilot"})
    res = client.post("/api/v1/models/events/scan", json={
        "discovered": [{"model_id": "Qwen/Qwen4-200B"}],  # 규모 상이하나 family 만 기준
        "criteria": ["family"],
    }).json()
    assert res["results"][0]["status"] == "candidate"
