"""데이터셋 고도화 테스트 — 문서 수집·URL 수집 정의·증강 추천·역번역 (impl/16th)."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.db import Base, get_db
from app.main import app
from app.services.augment import (
    back_translate_records,
    paraphrase_records,
    suggest_substitutions,
)
from app.services.collect import (
    build_document_record,
    collect_file,
    collect_url,
    extract_document_text,
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


DEFAULTS = {"task_type": "vuln_triage", "dataset_version": "v0.1.0", "source_type": "document_upload"}


# --- 문서 수집 ---

def test_extract_text_txt_md_html():
    assert extract_document_text("보고서 본문".encode(), "r.txt") == "보고서 본문"
    assert "취약점" in extract_document_text("# 취약점 요약".encode(), "r.md")
    html = "<html><script>bad()</script><body><h1>제목</h1><p>본문 단락</p></body></html>"
    out = extract_document_text(html.encode(), "r.html")
    assert "제목" in out and "본문 단락" in out and "bad()" not in out


def test_extract_text_docx():
    import io

    from docx import Document

    doc = Document()
    doc.add_paragraph("CVE-2024-0001 대응 보고서")
    buf = io.BytesIO()
    doc.save(buf)
    assert "CVE-2024-0001" in extract_document_text(buf.getvalue(), "report.docx")


def test_build_document_record_needs_annotation():
    rec = build_document_record("아파치 웹서버 취약점 상세 내용", "vuln.txt", dict(DEFAULTS))
    assert rec["messages"][0]["content"].startswith("다음 취약점 보고서")  # task 지시 프레임
    assert "needs_annotation" in rec["messages"][-1]["content"]  # 정답은 검수 단계
    assert rec["metadata"]["record_id"].startswith("r-")
    with pytest.raises(ValueError, match="no extractable text"):
        build_document_record("   ", "empty.txt", dict(DEFAULTS))


def test_collect_file_routing():
    doc = collect_file("보고서".encode(), "r.md", "canonical", dict(DEFAULTS))
    assert len(doc) == 1 and "needs_annotation" in doc[0]["messages"][-1]["content"]
    with pytest.raises(ValueError, match="unsupported file type"):
        collect_file(b"x", "malware.exe", "canonical", dict(DEFAULTS))


def test_collect_url_html_becomes_document():
    records = collect_url("https://ko.wikipedia.org/wiki/foo",
                          fetcher=lambda u: "<html><body><p>위협 문서 본문</p></body></html>")
    assert len(records) == 1
    assert "위협 문서 본문" in records[0]["messages"][0]["content"]
    assert records[0]["metadata"]["trust_tier"] == "T3_untrusted"


# --- 증강 고도화 ---

def _rec(rid, user):
    return {"messages": [{"role": "user", "content": user},
                         {"role": "assistant", "content": "분석 결과"}],
            "metadata": {"record_id": rid, "source_type": "manual",
                         "task_type": "alert_triage", "dataset_version": "v0.1.0"}}


def test_suggest_substitutions_frequency_and_dictionary():
    records = [_rec("r1", "아파치 웹서버에서 아파치 모듈 취약점"), _rec("r2", "아파치 로그의 피싱 링크")]
    suggestions = suggest_substitutions(records)
    keywords = {s["keyword"]: s for s in suggestions}
    assert "아파치" in keywords and keywords["아파치"]["frequency"] == 3
    assert "nginx" in keywords["아파치"]["candidates"]
    assert "피싱" in keywords  # 사전 매칭 항목만 추천


def test_back_translate_preserves_identifiers_and_lineage():
    fake = lambda text, src, tgt: f"[{tgt}]{text}"
    records = [_rec("r-bt", "CVE-2024-0001 및 T1059.001 관련 아파치 경보")]
    out = back_translate_records(records, fake)
    assert len(out) == 1
    aug = out[0]
    assert aug["metadata"]["record_id"] == "r-bt-bt-1" and aug["metadata"]["lineage_of"] == "r-bt"
    assert aug["metadata"]["quality_grade"] == "augmented"
    user = aug["messages"][0]["content"]
    assert "CVE-2024-0001" in user and "T1059.001" in user  # 식별자 복원
    assert aug["messages"][1]["content"] == "분석 결과"  # assistant 불변


def test_paraphrase_preserves_identifiers_and_lineage():
    fake = lambda text: f"[재구성] {text}"
    records = [_rec("r-pp", "CVE-2024-0001 및 T1059.001 관련 아파치 경보")]
    out = paraphrase_records(records, fake)
    assert len(out) == 1
    aug = out[0]
    assert aug["metadata"]["record_id"] == "r-pp-para-1" and aug["metadata"]["lineage_of"] == "r-pp"
    assert aug["metadata"]["quality_grade"] == "augmented"
    user = aug["messages"][0]["content"]
    assert "CVE-2024-0001" in user and "T1059.001" in user  # 식별자 복원
    assert aug["messages"][1]["content"] == "분석 결과"  # assistant 불변


def test_paraphrase_no_change_returns_empty_list():
    identity = lambda text: text
    records = [_rec("r-pp2", "변화 없는 문장")]
    assert paraphrase_records(records, identity) == []


# --- API ---

def _ingest_and_approve(client, rid, user):
    client.post("/api/v1/records/ingest", json={"records": [_rec(rid, user)]})
    client.post(f"/api/v1/records/{rid}/review", json={"action": "approve", "reviewer": "t"})


def test_suggestions_endpoint(client):
    _ingest_and_approve(client, "r-s1", "아파치 웹서버 아파치 취약점 경보")
    res = client.get("/api/v1/records/augment/suggestions").json()
    assert res["records_scanned"] == 1
    assert any(s["keyword"] == "아파치" for s in res["suggestions"])


def test_augment_backtranslate_unavailable_returns_503(client, monkeypatch):
    _ingest_and_approve(client, "r-b1", "아파치 경보")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://127.0.0.1:1")  # 미기동 포트
    res = client.post("/api/v1/records/augment", json={"method": "backtranslate"})
    assert res.status_code == 503 and "Ollama" in res.json()["detail"]


def test_augment_paraphrase_unavailable_returns_503(client, monkeypatch):
    _ingest_and_approve(client, "r-pp3", "아파치 경보")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://127.0.0.1:1")  # 미기동 포트
    res = client.post("/api/v1/records/augment", json={"method": "paraphrase"})
    assert res.status_code == 503 and "Ollama" in res.json()["detail"]


def test_upload_document_file(client):
    files = [("files", ("vuln-report.txt", "취약점 보고서 본문", "text/plain"))]
    res = client.post("/api/v1/records/upload", files=files,
                      data={"task_type": "vuln_triage"}).json()
    assert res["ingest"]["queued"] == 1
    rid = res["ingest"]["results"][0]["record_id"]
    detail = client.get(f"/api/v1/records/{rid}").json()
    assert "needs_annotation" in detail["payload"]["messages"][-1]["content"]
