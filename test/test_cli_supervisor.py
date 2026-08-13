"""CLI(F8)·Supervisor UI(F7) 테스트."""
import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from typer.testing import CliRunner

from app.cli import app as cli_app
from app.core import db as core_db
from app.main import app as web_app

runner = CliRunner()


@pytest.fixture(autouse=True)
def isolated_db(monkeypatch):
    """CLI 가 쓰는 전역 engine/SessionLocal 을 in-memory sqlite 로 교체."""
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    monkeypatch.setattr(core_db, "engine", engine)
    monkeypatch.setattr(core_db, "SessionLocal", sessionmaker(bind=engine, autoflush=False))
    yield


def make_record(rid):
    return {"messages": [{"role": "user", "content": f"질의 {rid}"},
                         {"role": "assistant", "content": f"답변 {rid}"}],
            "metadata": {"record_id": rid, "source_type": "manual",
                         "task_type": "alert_triage", "dataset_version": "v0.1.0"}}


def write_jsonl(path, items):
    path.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in items), encoding="utf-8")
    return str(path)


# --- CLI: dataset ---

def test_cli_dataset_validate_pass_and_fail(tmp_path):
    good = write_jsonl(tmp_path / "good.jsonl", [make_record("r-1")])
    assert runner.invoke(cli_app, ["dataset", "validate", good]).exit_code == 0
    bad_rec = make_record("r-2")
    bad_rec["messages"] = bad_rec["messages"][:1]
    bad = write_jsonl(tmp_path / "bad.jsonl", [bad_rec])
    assert runner.invoke(cli_app, ["dataset", "validate", bad]).exit_code == 1


def test_cli_dataset_convert_to_file(tmp_path):
    src = write_jsonl(tmp_path / "alpaca.jsonl", [{"instruction": "q", "output": "a"}])
    out = tmp_path / "canonical.jsonl"
    res = runner.invoke(cli_app, ["dataset", "convert", src, "--source", "alpaca",
                                  "--target", "canonical", "--out", str(out)])
    assert res.exit_code == 0
    assert json.loads(out.read_text().strip())["messages"][-1]["content"] == "a"


def test_cli_ingest_queue_review_flow(tmp_path):
    data = write_jsonl(tmp_path / "in.jsonl", [make_record("r-cli-1")])
    res = runner.invoke(cli_app, ["dataset", "ingest", data])
    assert res.exit_code == 0 and '"queued": 1' in res.output
    res = runner.invoke(cli_app, ["dataset", "queue"])
    assert "r-cli-1" in res.output
    res = runner.invoke(cli_app, ["dataset", "review", "r-cli-1",
                                  "--action", "approve", "--reviewer", "cli_01"])
    assert res.exit_code == 0 and '"approved"' in res.output


# --- CLI: models ---

def test_cli_models_seed_pin_manifest_plan():
    assert '"added": 12' in runner.invoke(cli_app, ["models", "seed", "--profile", "pilot"]).output
    res = runner.invoke(cli_app, ["models", "pin", "Qwen/Qwen3-14B", "--revision", "abc1234def"])
    assert res.exit_code == 0 and '"pinned"' in res.output
    assert '"abc1234def"' in runner.invoke(cli_app, ["models", "manifest"]).output
    plan = runner.invoke(cli_app, ["models", "download-plan", "Qwen/Qwen3-14B"])
    assert plan.output.startswith("hf download Qwen/Qwen3-14B")
    assert runner.invoke(cli_app, ["models", "pin", "no/such", "--revision", "abc1234def"]).exit_code == 1


def test_cli_models_scan(tmp_path):
    runner.invoke(cli_app, ["models", "seed", "--profile", "pilot"])
    scan_file = write_jsonl(tmp_path / "scan.jsonl", [{"model_id": "Qwen/Qwen3-15B-Preview"}])
    res = runner.invoke(cli_app, ["models", "scan", scan_file])
    assert '"candidate"' in res.output


# --- Supervisor UI ---

def test_supervisor_page_served():
    with TestClient(web_app) as client:
        res = client.get("/supervisor")
    assert res.status_code == 200
    body = res.text
    assert "SecuFTPL Supervisor" in body
    for marker in ["모델 선택", "사용용도", "검수 큐", "/api/v1/models/seed", "/api/v1/records/ingest"]:
        assert marker in body
