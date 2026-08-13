"""F12 — 평가지표 가이드·추천 테스트 (PRD, E11)."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.db import Base, get_db
from app.main import app
from app.services.eval_guide import METRIC_GUIDE, recommend_metrics


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


def test_recommend_metrics_known_task_type():
    guide = recommend_metrics("alert_triage")
    assert guide["recommended_metrics"] == ["severity_accuracy", "attack_f1", "json_valid_rate"]
    assert set(guide["guide"]) == set(guide["recommended_metrics"])
    assert guide["reliability_note"] is None


def test_recommend_metrics_unknown_task_type_falls_back_to_default():
    guide = recommend_metrics("unknown_task")
    assert guide["recommended_metrics"] == ["json_valid_rate", "attack_f1", "severity_accuracy"]


@pytest.mark.parametrize(("case_count", "expect_substr"), [
    (5, "30건 미만"),
    (50, "30~100건"),
    (500, "100건 이상"),
])
def test_recommend_metrics_case_count_reliability(case_count, expect_substr):
    guide = recommend_metrics("cti_extraction", case_count=case_count)
    assert expect_substr in guide["reliability_note"]


def test_all_metrics_have_guide_text():
    for key in ("json_valid_rate", "severity_accuracy", "exact_match_rate",
               "attack_precision", "attack_recall", "attack_f1"):
        assert METRIC_GUIDE.get(key)


def test_eval_guide_endpoint_default(client):
    res = client.get("/api/v1/tuning/eval-guide").json()
    assert res["task_type"] == "alert_triage"
    assert "attack_f1" in res["recommended_metrics"]


def test_eval_guide_endpoint_with_case_count(client):
    res = client.get("/api/v1/tuning/eval-guide?task_type=vuln_triage&case_count=10").json()
    assert res["task_type"] == "vuln_triage"
    assert "30건 미만" in res["reliability_note"]
