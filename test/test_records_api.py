"""검수 큐 API 테스트 (게이트 ⑤⑥⑨ 통합 + lineage 연쇄 폐기)."""
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


def make_record(rid, user="경보를 분석하라", lineage=None):
    meta = {"record_id": rid, "source_type": "internal_ir_report",
            "task_type": "alert_triage", "dataset_version": "v0.1.0"}
    if lineage:
        meta["lineage_of"] = lineage
    return {"messages": [{"role": "user", "content": user},
                         {"role": "assistant", "content": f"분석 결과 {rid}"}],
            "metadata": meta}


def test_ingest_sanitizes_and_queues(client):
    rec = make_record("r-1", user="호스트 FIN-WS-021 (10.0.0.5) 경보 분석")
    res = client.post("/api/v1/records/ingest", json={"records": [rec]}).json()
    assert res["queued"] == 1 and res["pseudonyms_added"] == 2
    queue = client.get("/api/v1/records/queue").json()
    assert queue["count"] == 1 and queue["items"][0]["record_id"] == "r-1"


def test_ingest_blocks_schema_error_and_exact_dup(client):
    bad = {"messages": [{"role": "user", "content": "질문만"}], "metadata": {}}
    rec = make_record("r-2")
    dup_same_content = make_record("r-3", user="경보를 분석하라")
    dup_same_content["messages"][1]["content"] = "분석 결과 r-2"  # 내용 동일 → 해시 중복
    r1 = client.post("/api/v1/records/ingest", json={"records": [bad, rec]}).json()
    assert r1["results"][0]["status"] == "rejected_gate" and r1["queued"] == 1
    r2 = client.post("/api/v1/records/ingest", json={"records": [dup_same_content]}).json()
    assert r2["results"][0]["status"] == "skipped_exact_duplicate"
    assert r2["results"][0]["existing"] == "r-2"


def test_ingest_skips_near_duplicate_in_batch(client):
    base = "고중요도 금융 단말에서 인코딩된 파워쉘 명령 실행이 탐지된 경보를 분석하고 심각도와 대응 절차를 판정하라"
    a = make_record("r-a", user=base)
    b = make_record("r-b", user=base + "!!")  # 문장부호만 다른 근접중복
    b["messages"][1]["content"] = a["messages"][1]["content"]  # 답변 동일
    res = client.post("/api/v1/records/ingest",
                      json={"records": [a, b], "near_dup_threshold": 0.6}).json()
    statuses = [r["status"] for r in res["results"]]
    assert statuses == ["queued", "skipped_near_duplicate"]


def test_review_approve_and_reject_cascade(client):
    orig = make_record("r-orig", user="원본 사고 경보 질의")
    aug = make_record("r-aug", user="원본 사고 경보 질의 증강본", lineage="r-orig")
    client.post("/api/v1/records/ingest", json={"records": [orig, aug]})
    ok = client.post("/api/v1/records/r-aug/review",
                     json={"action": "approve", "reviewer": "soc_01"}).json()
    assert ok["review_state"] == "approved"
    # 원본 반려 → 증강본은 이미 approved 여도... PRD: 반려 연쇄는 미반려 상태 대상 — approved 는 유지?
    # 정책: rejected 아닌 모든 자식 연쇄 폐기 (approved 포함) — API 구현 기준 검증
    rej = client.post("/api/v1/records/r-orig/review",
                      json={"action": "reject", "reviewer": "soc_01"}).json()
    assert rej["review_state"] == "rejected" and rej["cascaded_rejects"] == ["r-aug"]
    dup = client.post("/api/v1/records/r-orig/review",
                      json={"action": "approve", "reviewer": "soc_02"})
    assert dup.status_code == 409  # 재검수 차단


def test_record_detail_and_iso_utc_time(client):
    client.post("/api/v1/records/ingest", json={"records": [make_record("r-detail")]})
    detail = client.get("/api/v1/records/r-detail").json()
    assert detail["record_id"] == "r-detail" and detail["review_state"] == "pending"
    assert detail["payload"]["messages"][-1]["role"] == "assistant"  # 내용 확인 가능
    # 시간 표기 원칙: UTC ISO8601 (+00:00) — 화면에서 locale 변환
    assert detail["created_at"].endswith("+00:00")
    queue = client.get("/api/v1/records/queue").json()
    assert queue["items"][0]["created_at"].endswith("+00:00")
    assert client.get("/api/v1/records/no-such-id").status_code == 404


def test_delete_record_with_lineage_cascade(client):
    # 원본 + 증강본 적재 → 원본 삭제 시 연쇄 삭제
    client.post("/api/v1/records/ingest", json={"records": [
        make_record("r-del"), make_record("r-del-aug", user="증강 변형 질의", lineage="r-del")]})
    res = client.delete("/api/v1/records/r-del").json()
    assert res["deleted"] == "r-del" and res["cascaded_deletes"] == ["r-del-aug"]
    assert client.get("/api/v1/records/r-del").status_code == 404
    assert client.get("/api/v1/records/r-del-aug").status_code == 404
    assert client.delete("/api/v1/records/r-del").status_code == 404  # 재삭제 404


def test_review_not_found(client):
    res = client.post("/api/v1/records/nope/review",
                      json={"action": "approve", "reviewer": "x"})
    assert res.status_code == 404
