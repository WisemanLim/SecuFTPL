"""학습 워커·리더보드 상세 테스트 (impl/24th — wise-FP Stage7/8 준용)."""
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
    """dependency_overrides + 전역 SessionLocal 동시 교체 — 백그라운드 워커가 같은 DB 사용."""
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, autoflush=False)
    monkeypatch.setattr(core_db, "engine", engine)
    monkeypatch.setattr(core_db, "SessionLocal", TestSession)
    # 어댑터 산출물을 tmp 로
    from app.services import trainer

    monkeypatch.setattr(trainer, "ADAPTER_ROOT", tmp_path / "adapters")
    monkeypatch.setattr(trainer.time, "sleep", lambda s: None)  # 시뮬레이션 지연 제거
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


def _prepare(client):
    client.post("/api/v1/models/seed", json={"profile": "pilot"})
    client.post("/api/v1/models/Qwen/Qwen3-14B/pin", json={"revision": "abc1234def"})  # 학습 가능(pinned)
    client.post("/api/v1/records/ingest", json={"records": [{
        "messages": [
            {"role": "user", "content": "경보 분석"},
            {"role": "assistant",
             "content": '{"severity":"high","attack_mapping":[{"technique_id":"T1059.001"}]}'},
        ],
        "metadata": {"record_id": "r-tr1", "source_type": "manual",
                     "task_type": "alert_triage", "dataset_version": "v0.1.0"}}]})
    client.post("/api/v1/records/r-tr1/review", json={"action": "approve", "reviewer": "t"})


def test_job_trains_in_background_to_succeeded(client, tmp_path):
    _prepare(client)
    job = client.post("/api/v1/tuning/jobs",
                      json={"model_id": "Qwen/Qwen3-14B", "dataset_version": "v0.1.0"}).json()
    assert job["training"] == "background_started"
    # TestClient 는 응답 후 BackgroundTasks 실행 → 이 시점엔 학습 완료
    jobs = client.get("/api/v1/tuning/jobs").json()["jobs"]
    me = next(j for j in jobs if j["job_id"] == job["job_id"])
    assert me["status"] == "succeeded"
    assert me["adapter_uri"] and "adapters" in me["adapter_uri"]
    # 어댑터 manifest 생성 확인
    manifest = tmp_path / "adapters" / job["job_id"] / "adapter_manifest.json"
    assert manifest.exists() and "simulate" in manifest.read_text()
    # 이벤트 로그 — 학습 스텝 + 자동 평가 + 성공
    ev = client.get(f"/api/v1/tuning/jobs/{job['job_id']}/events").json()
    text = " ".join(e["message"] for e in ev["events"])
    assert "train start" in text and "loss=" in text
    assert "auto-eval" in text and "job succeeded" in text
    # 자동 평가 → 리더보드 반영
    lb = client.get("/api/v1/tuning/leaderboard").json()
    assert any(r["job_id"] == job["job_id"] for r in lb["items"])


def test_job_fails_without_approved_records(client):
    client.post("/api/v1/models/seed", json={"profile": "pilot"})
    # create_job 자체가 승인 0건이면 422 — 워커 진입 전 차단
    res = client.post("/api/v1/tuning/jobs",
                      json={"model_id": "Qwen/Qwen3-14B", "dataset_version": "v0.1.0"})
    assert res.status_code == 422


def test_leaderboard_detail(client):
    _prepare(client)
    job = client.post("/api/v1/tuning/jobs",
                      json={"model_id": "Qwen/Qwen3-14B", "dataset_version": "v0.1.0"}).json()
    detail = client.get("/api/v1/tuning/leaderboard/detail/Qwen/Qwen3-14B").json()
    assert detail["model_id"] == "Qwen/Qwen3-14B"
    assert detail["evaluations"][0]["job_id"] == job["job_id"]
    assert detail["jobs"][0]["status"] == "succeeded"
    assert client.get("/api/v1/tuning/leaderboard/detail/no/model").status_code == 404
    # 평가 결과 삭제 → 리더보드에서 제거
    eval_id = detail["evaluations"][0]["eval_id"]
    assert client.delete(f"/api/v1/tuning/leaderboard/{eval_id}").json()["deleted_eval_id"] == eval_id
    lb = client.get("/api/v1/tuning/leaderboard").json()
    assert all(r.get("job_id") != job["job_id"] for r in lb["items"])
    assert client.delete(f"/api/v1/tuning/leaderboard/{eval_id}").status_code == 404


def test_job_events_404(client):
    assert client.get("/api/v1/tuning/jobs/ft-none/events").status_code == 404


def test_progress_and_export(client, tmp_path):
    _prepare(client)
    job = client.post("/api/v1/tuning/jobs",
                      json={"model_id": "Qwen/Qwen3-14B", "dataset_version": "v0.1.0"}).json()
    jid = job["job_id"]
    me = next(j for j in client.get("/api/v1/tuning/jobs").json()["jobs"] if j["job_id"] == jid)
    assert me["status"] == "succeeded" and me["progress_pct"] == 100.0
    assert me["total_steps"] > 0  # 진행률 필드 노출
    # export — succeeded 잡 어댑터 tar.gz
    res = client.get(f"/api/v1/tuning/jobs/{jid}/export")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/gzip"
    assert f"{jid}.tar.gz" in res.headers["content-disposition"]
    assert len(res.content) > 0
    # 미존재/미완료 잡 export 차단
    assert client.get("/api/v1/tuning/jobs/ft-none/export").status_code == 404


def test_retry_and_delete_job(client):
    _prepare(client)
    job = client.post("/api/v1/tuning/jobs",
                      json={"model_id": "Qwen/Qwen3-14B", "dataset_version": "v0.1.0"}).json()
    jid = job["job_id"]
    # 이미 succeeded → 재실행 차단(409)
    assert client.post(f"/api/v1/tuning/jobs/{jid}/retry").status_code == 409
    # 삭제 → 이벤트 로그 연쇄 삭제
    assert client.delete(f"/api/v1/tuning/jobs/{jid}").json()["deleted"] == jid
    assert client.get(f"/api/v1/tuning/jobs/{jid}/events").status_code == 404
    assert client.delete(f"/api/v1/tuning/jobs/{jid}").status_code == 404  # 재삭제 404


def test_retry_stuck_job_reruns(client, monkeypatch):
    _prepare(client)
    # create_job 만 하고 워커 미투입한 stuck queued 잡을 직접 생성 (워커 없던 시절 재현)
    from app.core import db as core_db
    from app.services.tuning import create_job
    with core_db.SessionLocal() as s:
        stuck = create_job(s, "Qwen/Qwen3-14B", "v0.1.0")
        jid = stuck.job_id
    # 재실행 → 백그라운드 학습 → succeeded (TestClient 가 BackgroundTasks 실행)
    res = client.post(f"/api/v1/tuning/jobs/{jid}/retry").json()
    assert res["retry"] == "background_started"
    jobs = client.get("/api/v1/tuning/jobs").json()["jobs"]
    assert next(j for j in jobs if j["job_id"] == jid)["status"] == "succeeded"
