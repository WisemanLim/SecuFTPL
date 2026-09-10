"""E17·E18 테스트 (F20 DOC_PARSER 백엔드·F21 커버리지 합성, impl/49th·50th)."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.db import Base, get_db
from app.main import app
from app.services.collect import _docling_available, _extract_pdf
from app.services.rag_synth import (
    QUESTION_STYLES,
    coverage_synthesize,
    extract_keywords,
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


def _pdf_bytes() -> bytes:
    import io

    from pypdf import PdfWriter

    w = PdfWriter()
    w.add_blank_page(width=200, height=200)
    buf = io.BytesIO()
    w.write(buf)
    return buf.getvalue()


# --- F20 DOC_PARSER ---

def test_doc_parser_auto_falls_back_to_pypdf(monkeypatch):
    monkeypatch.setattr(settings, "doc_parser", "auto")
    # docling 미설치 환경 가정 — auto 는 조용히 pypdf 폴백 (빈 페이지 = 빈 문자열)
    if _docling_available():
        pytest.skip("docling installed — fallback path not applicable")
    assert _extract_pdf(_pdf_bytes(), "a.pdf") == ""


def test_doc_parser_explicit_docling_without_install_errors(monkeypatch):
    monkeypatch.setattr(settings, "doc_parser", "docling")
    if _docling_available():
        pytest.skip("docling installed")
    with pytest.raises(ValueError, match="docling 미설치"):
        _extract_pdf(_pdf_bytes(), "a.pdf")


def test_doc_parser_invalid_value(monkeypatch):
    monkeypatch.setattr(settings, "doc_parser", "nope")
    with pytest.raises(ValueError, match="invalid DOC_PARSER"):
        _extract_pdf(_pdf_bytes(), "a.pdf")


# --- F21 커버리지 합성 ---

CHUNKS = [
    "nginx 웹서버에서 웹셸 업로드 정황이 확인되었다 nginx 로그 분석 필요",
    "powershell 실행 이후 lateral movement 시도가 탐지되었다 powershell 차단 권고",
    "피싱 메일 첨부파일에서 매크로 실행이 확인되었다 피싱 대응 교육 필요",
]


def test_extract_keywords_frequency():
    kws = extract_keywords(CHUNKS, top_n=5)
    assert "nginx" in kws and "powershell" in kws


def test_coverage_synthesize_rotates_styles_and_reports():
    records, coverage = coverage_synthesize(CHUNKS, "alert_triage", "cov-v1", "doc://test")
    assert len(records) == 3
    # 질문 유형 회전 — 각 레코드 user 프롬프트에 서로 다른 스타일 문구
    prompts = [r["messages"][0]["content"] for r in records]
    assert QUESTION_STYLES[0] in prompts[0]
    assert QUESTION_STYLES[1] in prompts[1]
    assert QUESTION_STYLES[2] in prompts[2]
    assert "핵심 키워드" in prompts[0]
    assert coverage["chunks"] == 3
    assert coverage["covered"]  # 키워드 커버 집계 존재
    # 메타데이터는 기존 합성과 동일 계약(출처·hash 스탬핑)
    assert records[0]["metadata"]["source_type"] == "rag_synthesis"
    assert len(records[0]["metadata"]["source_hash_sha256"]) == 64


def test_rag_synthesize_endpoint_diversify(client):
    res = client.post("/api/v1/rag/synthesize", json={
        "documents": [{"title": "threat-report", "text": " ".join(CHUNKS)}],
        "task_type": "cti_extraction", "dataset_version": "cov-v2",
        "chunk_size": 200, "diversify": True}).json()
    assert res["ingest"]["queued"] >= 1
    assert res["coverage"][0]["document"] == "threat-report"
    assert "keywords" in res["coverage"][0]
