"""E15 정제 게이트 고도화 테스트 (F18 — 13-gram 디컨탬·DPI 출처 필드, impl/47th)."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.db import Base, get_db
from app.main import app
from app.services.dedup import decontaminate


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


def _rec(rid, version, user, **extra_meta):
    return {"messages": [{"role": "user", "content": user},
                         {"role": "assistant", "content": f"분석 결과 {rid}"}],
            "metadata": {"record_id": rid, "source_uri": "test://fixture",
                         "source_hash_sha256": "f" * 64, "source_type": "manual",
                         "task_type": "alert_triage", "dataset_version": version, **extra_meta}}


LONG = ("공격자가 nginx 웹서버의 취약한 업로드 모듈을 통해 웹셸을 배포하고 "
        "권한 상승 후 내부망으로 측면 이동을 시도한 정황이 로그에서 확인되었다 " * 2)


def test_decontaminate_flags_shared_ngram():
    train = [_rec("r-t1", "tr", LONG), _rec("r-t2", "tr", "완전히 다른 짧은 경보")]
    evals = [_rec("r-e1", "ev", LONG + " 추가 문장")]
    report = decontaminate(train, evals, k=13)
    assert report["contaminated_count"] == 1
    assert report["contaminated"][0]["record_id"] == "r-t1"
    assert report["k"] == 13


def test_decontam_endpoint(client):
    client.post("/api/v1/records/ingest", json={"records": [
        _rec("r-a1", "train-v1", LONG), _rec("r-b1", "eval-v1", LONG + " 변형")]})
    for rid in ("r-a1", "r-b1"):
        client.post(f"/api/v1/records/{rid}/review", json={"action": "approve", "reviewer": "t"})
    res = client.get("/api/v1/datasets/decontam",
                     params={"train_version": "train-v1", "eval_version": "eval-v1"}).json()
    assert res["contaminated_count"] == 1
    assert client.get("/api/v1/datasets/decontam",
                      params={"train_version": "x", "eval_version": "eval-v1"}).status_code == 404
    assert client.get("/api/v1/datasets/decontam",
                      params={"train_version": "train-v1", "eval_version": "eval-v1",
                              "k": 99}).status_code == 422


def test_dpi_fields_roundtrip_to_manifest(client):
    rec = _rec("r-dpi1", "dpi-v1", "경보 분석", creator="CISA",
               license_url="https://example.org/license", provenance_notes="KEV feed 수집")
    client.post("/api/v1/records/ingest", json={"records": [rec]})
    client.post("/api/v1/records/r-dpi1/review", json={"action": "approve", "reviewer": "t"})
    manifest = client.get("/api/v1/datasets/export/manifest",
                          params={"dataset_version": "dpi-v1"}).json()
    entry = manifest["sources"]["test://fixture"]
    assert entry["creator"] == "CISA"
    assert entry["license_url"] == "https://example.org/license"
    assert entry["provenance_notes"] == "KEV feed 수집"
