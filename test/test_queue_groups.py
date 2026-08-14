"""검수 큐 그룹핑 UX 테스트 — 그룹(dataset_version) 요약 + 세부 필터 (PRD §7.15, impl/42nd)."""
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


def _rec(rid, version, user, source_uri="test://fixture"):
    return {"messages": [{"role": "user", "content": user},
                         {"role": "assistant", "content": f"분석 결과 {rid}"}],
            "metadata": {"record_id": rid, "source_uri": source_uri,
                         "source_hash_sha256": "f" * 64, "source_type": "manual",
                         "task_type": "alert_triage", "dataset_version": version}}


def test_queue_groups_aggregation(client):
    client.post("/api/v1/records/ingest", json={"records": [
        _rec("r-g1", "pipeline-A", "경보 하나"),
        _rec("r-g2", "pipeline-A", "경보 둘", source_uri="test://other"),
        _rec("r-g3", "pipeline-B", "경보 셋"),
    ]})
    data = client.get("/api/v1/records/queue/groups").json()
    assert data["group_count"] == 2 and data["total"] == 3
    by_key = {g["dataset_version"]: g for g in data["groups"]}
    a = by_key["pipeline-A"]
    assert a["count"] == 2
    assert a["grades"] == {"silver": 2}
    assert a["task_types"] == {"alert_triage": 2}
    assert a["sources"] == {"test://fixture": 1, "test://other": 1}
    assert a["first_created_at"] and a["last_created_at"]
    assert by_key["pipeline-B"]["count"] == 1


def test_queue_filter_by_dataset_version(client):
    client.post("/api/v1/records/ingest", json={"records": [
        _rec("r-f1", "pipeline-A", "경보 하나"),
        _rec("r-f2", "pipeline-B", "경보 둘"),
    ]})
    data = client.get("/api/v1/records/queue", params={"dataset_version": "pipeline-A"}).json()
    assert data["count"] == 1 and data["items"][0]["record_id"] == "r-f1"
    # 필터 미지정 = 전체 (기존 동작 유지)
    assert client.get("/api/v1/records/queue").json()["count"] == 2


def test_review_group_bulk_approve(client):
    client.post("/api/v1/records/ingest", json={"records": [
        _rec("r-b1", "pipeline-A", "경보 하나"),
        _rec("r-b2", "pipeline-A", "경보 둘"),
        _rec("r-b3", "pipeline-B", "경보 셋"),
    ]})
    res = client.post("/api/v1/records/queue/review-group",
                      json={"dataset_version": "pipeline-A", "action": "approve", "reviewer": "t"}).json()
    assert res["reviewed_count"] == 2 and set(res["reviewed"]) == {"r-b1", "r-b2"}
    # 다른 그룹은 pending 유지, 개별 검수 경로도 그대로 동작
    assert client.get("/api/v1/records/queue").json()["count"] == 1
    ind = client.post("/api/v1/records/r-b3/review",
                      json={"action": "approve", "reviewer": "t"}).json()
    assert ind["review_state"] == "approved"
    assert client.get("/api/v1/records/queue", params={"state": "approved"}).json()["count"] == 3


def test_review_group_bulk_reject_cascades_lineage(client):
    client.post("/api/v1/records/ingest", json={"records": [_rec("r-o1", "pipeline-A", "아파치 웹서버 경보")]})
    client.post("/api/v1/records/r-o1/review", json={"action": "approve", "reviewer": "t"})
    client.post("/api/v1/records/augment", json={"substitutions": {"아파치": "nginx"}})
    # 증강본은 pending — 증강본만 있는 그룹을 일괄 반려해도 원본(approved)은 유지
    res = client.post("/api/v1/records/queue/review-group",
                      json={"dataset_version": "pipeline-A", "action": "reject", "reviewer": "t"}).json()
    assert res["review_state"] == "rejected" and res["reviewed_count"] == 1
    assert client.get("/api/v1/records/r-o1").json()["review_state"] == "approved"
    assert client.get("/api/v1/records/queue", params={"state": "rejected"}).json()["count"] == 1


def test_review_group_404_when_no_pending(client):
    res = client.post("/api/v1/records/queue/review-group",
                      json={"dataset_version": "nope", "action": "approve", "reviewer": "t"})
    assert res.status_code == 404


def test_queue_groups_empty_and_state(client):
    assert client.get("/api/v1/records/queue/groups").json()["group_count"] == 0
    client.post("/api/v1/records/ingest", json={"records": [_rec("r-s1", "pipeline-A", "경보")]})
    client.post("/api/v1/records/r-s1/review", json={"action": "approve", "reviewer": "t"})
    assert client.get("/api/v1/records/queue/groups").json()["group_count"] == 0  # pending 기본
    approved = client.get("/api/v1/records/queue/groups", params={"state": "approved"}).json()
    assert approved["group_count"] == 1 and approved["groups"][0]["count"] == 1
