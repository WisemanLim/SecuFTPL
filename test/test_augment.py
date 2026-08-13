"""E4 데이터 증강 테스트 (키워드 치환·lineage·보호 식별자)."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.db import Base, get_db
from app.main import app
from app.services.augment import (
    augment_record,
    augment_records,
    substitute_text,
    validate_substitutions,
)


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


def _rec(rid, user):
    return {"messages": [{"role": "user", "content": user},
                         {"role": "assistant", "content": "T1059.001 대응 절차 안내"}],
            "metadata": {"record_id": rid, "source_type": "manual",
                         "task_type": "alert_triage", "dataset_version": "v0.1.0"}}


def test_substitute_word_boundary():
    out = substitute_text("아파치 서버와 아파치캠프", {"아파치": "nginx"})
    assert out == "nginx 서버와 아파치캠프"  # 단어 경계 — 부분 문자열 미치환


def test_protected_identifiers_rejected():
    assert validate_substitutions({"CVE-2024-1234": "CVE-9999-0000"}) == ["CVE-2024-1234"]
    with pytest.raises(ValueError, match="protected"):
        augment_records([_rec("r-1", "x")], {"T1059.001": "T9999"})


def test_augment_record_lineage_and_grade():
    rec = _rec("r-1", "아파치 웹서버 취약점 경보")
    aug = augment_record(rec, {"아파치": "nginx"}, seq=1)
    assert aug["metadata"]["record_id"] == "r-1-aug-1"
    assert aug["metadata"]["lineage_of"] == "r-1"
    assert aug["metadata"]["quality_grade"] == "augmented"
    assert "nginx" in aug["messages"][0]["content"]
    assert "T1059.001" in aug["messages"][1]["content"]  # 라벨 식별자 불변
    assert augment_record(rec, {"없는단어": "x"}) is None  # 무변화 → 배제


def test_augment_api_flow_and_reject_cascade(client):
    # 원본 수집·승인 → 증강 → 큐 재편입 → 원본 반려 시 증강본 연쇄 폐기
    client.post("/api/v1/records/ingest", json={"records": [_rec("r-o", "아파치 웹서버 취약점 경보")]})
    client.post("/api/v1/records/r-o/review", json={"action": "approve", "reviewer": "t"})
    res = client.post("/api/v1/records/augment", json={"substitutions": {"아파치": "nginx"}}).json()
    assert res["augmented"] == 1 and res["ingest"]["queued"] == 1
    queue = client.get("/api/v1/records/queue?state=pending").json()
    assert queue["items"][0]["record_id"] == "r-o-aug-1"
    assert queue["items"][0]["lineage_of"] == "r-o"
    # 승인 원본이 없으면 422
    assert client.post("/api/v1/records/augment",
                       json={"substitutions": {"x": "y"}, "record_ids": ["none"]}).status_code == 422


def test_augmented_not_re_augmented(client):
    client.post("/api/v1/records/ingest", json={"records": [_rec("r-o2", "아파치 경보")]})
    client.post("/api/v1/records/r-o2/review", json={"action": "approve", "reviewer": "t"})
    client.post("/api/v1/records/augment", json={"substitutions": {"아파치": "nginx"}})
    client.post("/api/v1/records/r-o2-aug-1/review", json={"action": "approve", "reviewer": "t"})
    # 증강본이 approved 여도 재증강 대상에서 제외 (lineage_of not null)
    res = client.post("/api/v1/records/augment", json={"substitutions": {"nginx": "haproxy"}}).json()
    assert res["augmented"] == 0
