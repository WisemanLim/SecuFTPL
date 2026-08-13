"""수집 채널 테스트 (PRD §7.3 수집 채널 — 파일 멀티·디렉토리·URL)."""
import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.db import Base, get_db
from app.main import app
from app.services.collect import (
    collect_dir,
    collect_url,
    normalize_records,
    parse_payload,
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


def rec(rid, user="경보 분석"):
    return {"messages": [{"role": "user", "content": user},
                         {"role": "assistant", "content": f"결과 {rid}"}],
            "metadata": {"record_id": rid, "source_type": "manual",
                         "task_type": "alert_triage", "dataset_version": "v0.1.0"}}


def jsonl(items):
    return "".join(json.dumps(x, ensure_ascii=False) + "\n" for x in items)


# --- 서비스 ---

def test_parse_payload_jsonl_and_json():
    assert len(parse_payload(jsonl([rec("a"), rec("b")]))) == 2
    assert len(parse_payload(json.dumps([rec("a")]), "x.json")) == 1
    assert len(parse_payload(json.dumps(rec("a")), "x.json")) == 1


def test_normalize_records_autofills_record_id_and_defaults():
    alpaca = [{"instruction": "질문", "output": "답"}]
    out = normalize_records(alpaca, "alpaca", {"task_type": "policy_qa", "dataset_version": "v1",
                                               "source_type": "file_upload"})
    meta = out[0]["metadata"]
    assert meta["record_id"].startswith("r-") and meta["task_type"] == "policy_qa"


def test_collect_dir_glob_and_partial_errors(tmp_path):
    (tmp_path / "a.jsonl").write_text(jsonl([rec("d1"), rec("d2")]), encoding="utf-8")
    (tmp_path / "bad.jsonl").write_text("{invalid json", encoding="utf-8")
    records, reports = collect_dir(str(tmp_path), "*.jsonl")
    assert len(records) == 2
    statuses = {r["file"]: r["status"] for r in reports}
    assert statuses["a.jsonl"] == "ok" and statuses["bad.jsonl"].startswith("error")
    with pytest.raises(ValueError, match="not a directory"):
        collect_dir(str(tmp_path / "nope"))


def test_collect_url_whitelist_and_ssrf_guard():
    with pytest.raises(ValueError, match="whitelist"):
        collect_url("https://evil.example.com/data.jsonl")
    with pytest.raises(ValueError, match="scheme"):
        collect_url("file:///etc/passwd")
    # 화이트리스트 도메인 + fetcher 주입(네트워크 미사용) → T3_untrusted 태깅
    records = collect_url("https://raw.githubusercontent.com/org/repo/data.jsonl",
                          fetcher=lambda u: jsonl([rec("web1")]))
    assert records[0]["metadata"]["trust_tier"] == "T3_untrusted"  # 기본 태깅
    assert records[0]["metadata"]["source_type"] == "manual"  # 레코드 명시값 우선 (기본값은 미지정 시만)
    bare = collect_url("https://raw.githubusercontent.com/org/repo/bare.jsonl",
                       fetcher=lambda u: json.dumps({"messages": rec("w2")["messages"]}) + "\n")
    assert bare[0]["metadata"]["source_type"] == "web_collect"  # 미지정 → 기본값 적용


# --- API ---

def test_upload_multi_files(client):
    files = [
        ("files", ("one.jsonl", jsonl([rec("u1")]), "application/json")),
        ("files", ("two.json", json.dumps([rec("u2")]), "application/json")),
        ("files", ("bad.jsonl", "{oops", "application/json")),
    ]
    res = client.post("/api/v1/records/upload", files=files,
                      data={"source_format": "canonical"}).json()
    assert res["ingest"]["queued"] == 2
    assert [f["status"] for f in res["files"]][2].startswith("error")
    # 전부 실패 → 422
    bad = client.post("/api/v1/records/upload",
                      files=[("files", ("x.jsonl", "{", "application/json"))])
    assert bad.status_code == 422


def test_collect_dir_endpoint(client, tmp_path):
    (tmp_path / "d.jsonl").write_text(jsonl([rec("dir1")]), encoding="utf-8")
    res = client.post("/api/v1/records/collect/dir", json={"path": str(tmp_path)}).json()
    assert res["ingest"]["queued"] == 1
    assert client.post("/api/v1/records/collect/dir",
                       json={"path": str(tmp_path / "none")}).status_code == 422


def test_collect_url_endpoint_rejects_non_whitelist(client):
    res = client.post("/api/v1/records/collect/url",
                      json={"url": "https://not-allowed.io/x.jsonl"})
    assert res.status_code == 422 and "whitelist" in res.json()["detail"]
