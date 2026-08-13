"""ops cron 배선 플랜 생성 테스트 (PRD F5·F2 §7.9, E6)."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.db import Base, get_db
from app.main import app
from app.services.ops_cron import cron_plan


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


def test_cron_plan_includes_both_schedules_and_endpoints():
    plan = cron_plan("http://127.0.0.1:8000")
    assert settings.ft_trigger_schedule_cron in plan
    assert settings.hf_polling_cron in plan
    assert "/api/v1/batch/run" in plan
    assert "/api/v1/models/events/scan" in plan
    assert "crontab -e" in plan  # 실행/설치 없음 안내


def test_cron_plan_uses_custom_base_url_and_strips_trailing_slash():
    plan = cron_plan("http://internal-host:9000/")
    assert "http://internal-host:9000/api/v1/batch/run" in plan
    assert "http://internal-host:9000//api" not in plan


def test_cron_plan_endpoint_default_and_custom(client):
    res = client.get("/api/v1/batch/cron-plan").json()
    assert res["base_url"] == "http://127.0.0.1:8000"
    assert "/api/v1/batch/run" in res["command"]

    res2 = client.get("/api/v1/batch/cron-plan?base_url=http://ops-host:8080").json()
    assert "http://ops-host:8080/api/v1/models/events/scan" in res2["command"]
