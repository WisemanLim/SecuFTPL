"""E3 튜닝·평가·리더보드 테스트."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.db import Base, get_db
from app.main import app
from app.services.evaluate import evaluate_predictions, set_f1


@pytest.fixture()
def client(monkeypatch, tmp_path):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, autoflush=False)
    # 잡 생성 시 백그라운드 학습 워커가 전역 SessionLocal 사용 → 동일 in-memory DB 로 교체
    from app.core import db as core_db
    from app.services import trainer
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


def _approve_one(client, rid="r-t1"):
    client.post("/api/v1/records/ingest", json={"records": [{
        "messages": [{"role": "user", "content": f"경보 {rid}"},
                     {"role": "assistant", "content": f"분석 {rid}"}],
        "metadata": {"record_id": rid, "source_uri": "test://fixture", "source_hash_sha256": "f" * 64, "source_type": "manual",
                     "task_type": "alert_triage", "dataset_version": "v0.1.0"},
    }]})
    client.post(f"/api/v1/records/{rid}/review", json={"action": "approve", "reviewer": "t"})


# --- 평가 러너 (순수 계산) ---

def test_set_f1_exact_and_empty():
    assert set_f1(["T1059"], ["T1059"]) == (1.0, 1.0, 1.0)
    assert set_f1([], []) == (1.0, 1.0, 1.0)  # 빈=빈 → 완벽 일치
    assert set_f1(["T1059"], []) == (0.0, 0.0, 0.0)  # 오탐만 존재
    p, r, f1 = set_f1(["T1059", "T1566"], ["T1059"])
    assert (p, r) == (0.5, 1.0) and 0 < f1 < 1


def test_evaluate_predictions_metrics():
    rows = [
        {"expected": {"severity": "high", "attack_ids": ["T1059.001"]},
         "prediction": '{"severity": "high", "attack_ids": ["T1059.001"]}'},
        {"expected": {"severity": "low", "attack_ids": []},
         "prediction": "not-json"},
    ]
    m = evaluate_predictions(rows)
    assert m["cases"] == 2
    assert m["json_valid_rate"] == 0.5
    assert m["severity_accuracy"] == 0.5
    assert m["attack_f1"] == 1.0  # row2: pred []=gold [] → f1 1.0
    assert m["exact_match_rate"] == 0.5


# --- 잡 오케스트레이션 ---

def test_job_requires_model_and_approved_records(client):
    res = client.post("/api/v1/tuning/jobs",
                      json={"model_id": "no/model", "dataset_version": "v0.1.0"})
    assert res.status_code == 422  # 모델 미등록
    client.post("/api/v1/models/seed", json={"profile": "pilot"})
    res = client.post("/api/v1/tuning/jobs",
                      json={"model_id": "Qwen/Qwen3-14B", "dataset_version": "v0.1.0"})
    assert res.status_code == 422  # 승인 레코드 없음


def test_job_creation_and_plan(client):
    client.post("/api/v1/models/seed", json={"profile": "pilot"})
    client.post("/api/v1/models/Qwen/Qwen3-14B/pin", json={"revision": "abc1234def"})
    _approve_one(client)
    job = client.post("/api/v1/tuning/jobs",
                      json={"model_id": "Qwen/Qwen3-14B", "dataset_version": "v0.1.0"}).json()
    assert job["record_count"] == 1  # 백그라운드 워커가 즉시 학습 → 상태는 test_trainer 가 검증
    plan = client.get(f"/api/v1/tuning/jobs/{job['job_id']}/plan").json()["plan"]
    assert "base_model: Qwen/Qwen3-14B" in plan and "method: qlora" in plan
    assert "load_in_4bit: True" in plan and "lora_r: 16" in plan
    # 학습 완료된 잡 재-complete 는 409 (외부 worker 콜백 경로)
    assert client.post(f"/api/v1/tuning/jobs/{job['job_id']}/complete",
                       json={"status": "failed"}).status_code == 409


def test_eval_template_from_approved_records(client):
    # 정답 JSON 레코드 승인 → 템플릿 행 생성 (attack_mapping → attack_ids 추출)
    client.post("/api/v1/records/ingest", json={"records": [{
        "messages": [
            {"role": "user", "content": "경보 분석"},
            {"role": "assistant", "content":
             '{"severity":"high","attack_mapping":[{"technique_id":"T1059.001"}]}'},
        ],
        "metadata": {"record_id": "r-et1", "source_uri": "test://fixture", "source_hash_sha256": "f" * 64, "source_type": "manual",
                     "task_type": "alert_triage", "dataset_version": "v0.1.0"}}]})
    client.post("/api/v1/records/r-et1/review", json={"action": "approve", "reviewer": "t"})
    # 비 JSON 정답 레코드 → skipped
    _approve_one(client, "r-et2")
    t = client.get("/api/v1/tuning/eval-template?dataset_version=v0.1.0").json()
    assert t["count"] == 1 and t["skipped_unparsable"] == 1
    row = t["rows"][0]
    assert row["expected"] == {"severity": "high", "attack_ids": ["T1059.001"]}
    assert row["prediction"] == row["expected"]  # 수정 가능한 출발점
    # 자동 입력 행 그대로 평가 → 게이트 통과 흐름
    client.post("/api/v1/tuning/evaluate", json={
        "model_id": "m-et", "dataset_version": "v0.1.0", "rows": t["rows"]})
    gate = client.post("/api/v1/batch/gate",
                       json={"model_id": "m-et", "dataset_version": "v0.1.0"}).json()
    assert gate["passed"] is True


def test_evaluate_endpoint_and_leaderboard_ranking(client):
    rows = [{"expected": {"severity": "high", "attack_ids": ["T1059"]},
             "prediction": {"severity": "high", "attack_ids": ["T1059"]}}]
    client.post("/api/v1/tuning/evaluate", json={
        "model_id": "model-A", "dataset_version": "v1", "rows": rows})  # baseline f1=1.0
    client.post("/api/v1/tuning/evaluate", json={
        "model_id": "model-B", "dataset_version": "v1", "job_id": "ft-x",
        "rows": [{"expected": {"severity": "high", "attack_ids": ["T1059"]},
                  "prediction": {"severity": "low", "attack_ids": []}}]})
    lb = client.get("/api/v1/tuning/leaderboard?dataset_version=v1").json()
    assert lb["count"] == 2
    assert lb["items"][0]["model_id"] == "model-A"  # attack_f1 내림차순
    assert lb["items"][0]["baseline"] is True
    assert lb["items"][1]["job_id"] == "ft-x"
