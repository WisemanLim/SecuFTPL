"""E5 Agent 환류·E6 야간 배치 테스트."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core import db as core_db
from app.core.config import settings
from app.core.db import Base, get_db
from app.main import app


@pytest.fixture()
def client(monkeypatch, tmp_path):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, autoflush=False)
    from app.services import trainer

    # 배치가 생성한 잡은 이제 즉시 학습 디스패치됨(F9 admit_or_queue) — 백그라운드 워커도
    # 테스트용 in-memory DB 를 사용하도록 전역 SessionLocal 교체 필요.
    monkeypatch.setattr(core_db, "engine", engine)
    monkeypatch.setattr(core_db, "SessionLocal", TestSession)
    monkeypatch.setattr(trainer, "ADAPTER_ROOT", tmp_path / "adapters")
    monkeypatch.setattr(trainer.time, "sleep", lambda s: None)
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


FB = {"question": "이 경보 원인은?", "answer": "인코딩된 파워쉘 실행", "score": "up",
      "task_type": "alert_triage", "model_version": "qwen3-14b-ft1"}


# --- E5: 피드백 환류 ---

def test_feedback_ingests_to_review_queue(client):
    res = client.post("/api/v1/feedback", json=FB).json()
    assert res["record_id"].startswith("fb-")
    assert res["ingest"]["queued"] == 1
    queue = client.get("/api/v1/records/queue?state=pending").json()
    assert queue["items"][0]["record_id"] == res["record_id"]
    # 동일 질의/답변 재제출 → 중복 차단 (record_id = 내용 해시)
    dup = client.post("/api/v1/feedback", json=FB).json()
    assert dup["ingest"]["results"][0]["status"] == "skipped_exact_duplicate"


def test_feedback_scale_validation_and_likert(client):
    bad = client.post("/api/v1/feedback", json={**FB, "score": 3})  # binary 에 3
    assert bad.status_code == 422
    ok = client.post("/api/v1/feedback",
                     json={**FB, "question": "다른 질문", "scale": "likert5", "score": 4})
    assert ok.status_code == 200


def test_feedback_down_and_stats(client):
    client.post("/api/v1/feedback", json=FB)
    client.post("/api/v1/feedback",
                json={**FB, "question": "부정확한 답의 질문", "score": "down",
                      "reason_tags": ["부정확"]})
    stats = client.get("/api/v1/feedback/stats").json()
    assert stats["total"] == 2 and stats["up"] == 1 and stats["down"] == 1
    assert stats["up_ratio"] == 0.5
    assert stats["by_state"]["pending"] == 2


def test_feedback_sanitized(client):
    res = client.post("/api/v1/feedback", json={
        **FB, "question": "호스트 FIN-WS-021 (10.0.0.5) 에서 경보"}).json()
    assert res["ingest"]["pseudonyms_added"] == 2  # 게이트 ⑤ 동일 적용


# --- E6: 야간 배치 ---

def _prepare(client, approve=1):
    client.post("/api/v1/models/seed", json={"profile": "pilot"})
    client.post("/api/v1/models/Qwen/Qwen3-14B/pin", json={"revision": "abc1234def"})
    for i in range(approve):
        rid = f"r-b{i}"
        client.post("/api/v1/records/ingest", json={"records": [{
            "messages": [{"role": "user", "content": f"경보 {rid} 분석 요청 상세 내용"},
                         {"role": "assistant", "content": f"분석 결과 {rid}"}],
            "metadata": {"record_id": rid, "source_type": "manual",
                         "task_type": "alert_triage", "dataset_version": "v0.1.0"}}]})
        client.post(f"/api/v1/records/{rid}/review", json={"action": "approve", "reviewer": "t"})


def test_batch_schedule_mode_creates_jobs_for_pinned(client):
    _prepare(client)
    run = client.post("/api/v1/batch/run", json={"mode": "schedule"}).json()
    assert run["status"] == "jobs_created" and len(run["jobs"]) == 1  # pinned 1개
    jobs = client.get("/api/v1/tuning/jobs").json()
    assert jobs["jobs"][0]["triggered_by"] == "batch"
    runs = client.get("/api/v1/batch/runs").json()
    assert runs["runs"][0]["status"] == "jobs_created"


def test_batch_record_count_threshold_skips(client):
    _prepare(client, approve=1)  # threshold 500 미달
    run = client.post("/api/v1/batch/run", json={"mode": "record_count"}).json()
    assert run["status"] == "skipped_below_threshold"
    assert run["detail"]["threshold"] == 500
    sr = client.get("/api/v1/batch/should-run?mode=record_count").json()
    assert sr["should_run"] is False


def test_batch_no_pinned_model_skips(client):
    client.post("/api/v1/records/ingest", json={"records": [{
        "messages": [{"role": "user", "content": "경보"},
                     {"role": "assistant", "content": "분석"}],
        "metadata": {"record_id": "r-x", "source_type": "manual",
                     "task_type": "alert_triage", "dataset_version": "v0.1.0"}}]})
    client.post("/api/v1/records/r-x/review", json={"action": "approve", "reviewer": "t"})
    run = client.post("/api/v1/batch/run", json={"mode": "schedule"}).json()
    assert run["status"] == "skipped_no_pinned_model"


def test_evaluation_gate_pass_block_regression(client):
    good = {"cases": 10, "json_valid_rate": 0.99, "severity_accuracy": 0.9,
            "exact_match_rate": 0.5, "attack_f1": 0.8,
            "attack_precision": 0.8, "attack_recall": 0.8}
    # 1차 결과 → 게이트 통과
    client.post("/api/v1/tuning/evaluate", json={
        "model_id": "m", "dataset_version": "v1",
        "rows": [{"expected": {"severity": "high", "attack_ids": ["T1"]},
                  "prediction": {"severity": "high", "attack_ids": ["T1"]}}]})
    gate = client.post("/api/v1/batch/gate", json={"model_id": "m", "dataset_version": "v1"}).json()
    assert gate["passed"] is True
    # 2차(v2)에서 회귀(f1 하락) → 차단
    from app.services import tuning as tsvc  # noqa: F401
    client.post("/api/v1/tuning/evaluate", json={
        "model_id": "m", "dataset_version": "v2",
        "rows": [{"expected": {"severity": "high", "attack_ids": ["T1"]},
                  "prediction": {"severity": "high", "attack_ids": []}}]})
    gate2 = client.post("/api/v1/batch/gate", json={"model_id": "m", "dataset_version": "v2"}).json()
    assert gate2["passed"] is False and "regression" in gate2["reason"]
    # 결과 없는 버전 → 차단
    gate3 = client.post("/api/v1/batch/gate", json={"model_id": "m", "dataset_version": "v9"}).json()
    assert gate3["passed"] is False
    assert good["attack_f1"] == 0.8  # fixture sanity
