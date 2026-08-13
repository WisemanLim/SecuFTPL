"""secuftpl — 파이프라인 CLI (PRD F8, §7.10).

frontend 부재 환경에서 각 파이프라인을 실행하는 진입점. API 서버 불필요 — DB 직접 접근.
설치 후: `secuftpl --help` (또는 `uv run secuftpl ...`)

  secuftpl dataset validate data.jsonl
  secuftpl dataset convert data.jsonl --source alpaca --target canonical --out out.jsonl
  secuftpl dataset ingest data.jsonl
  secuftpl dataset queue --state pending
  secuftpl dataset review r-0001 --action approve --reviewer soc_01
  secuftpl models seed --profile pilot
  secuftpl models list --status registered
  secuftpl models pin Qwen/Qwen3-14B --revision <hash>
  secuftpl models manifest
  secuftpl models scan discovered.jsonl
  secuftpl models download-plan Qwen/Qwen3-14B
"""
import json
from pathlib import Path

import typer

from app.core import db as core_db
from app.core.config import settings

app = typer.Typer(help="SecuFTPL 파이프라인 CLI (PRD F8)")
dataset_app = typer.Typer(help="데이터셋 파이프라인: 검증·변환·수집·검수·증강")
models_app = typer.Typer(help="모델 레지스트리: 시드·pin·manifest·이벤트 스캔")
tune_app = typer.Typer(help="튜닝 잡·평가·리더보드 (E3)")
batch_app = typer.Typer(help="야간 배치 (E6)")
app.add_typer(dataset_app, name="dataset")
app.add_typer(models_app, name="models")
app.add_typer(tune_app, name="tune")
app.add_typer(batch_app, name="batch")


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _echo(obj: dict | list) -> None:
    typer.echo(json.dumps(obj, ensure_ascii=False, indent=2, default=str))


def _session():
    core_db.init_db()
    return core_db.SessionLocal()


# --- dataset ---

@dataset_app.command("validate")
def dataset_validate(path: Path):
    """canonical JSONL 배치 검증 (정제 게이트 리포트). invalid 존재 시 exit 1."""
    from app.services.gate import validate_records

    report = validate_records(_read_jsonl(path))
    _echo(report)
    raise typer.Exit(1 if report["invalid"] else 0)


@dataset_app.command("convert")
def dataset_convert(
    path: Path,
    source: str = typer.Option(...),
    target: str = typer.Option(...),
    out: Path | None = typer.Option(None, help="미지정 시 stdout"),
):
    """포맷 변환 (alpaca/sharegpt/openai-chat ↔ canonical, export: dpo-pairs/eval-set)."""
    from app.services.formats import convert

    items = convert(_read_jsonl(path), source, target)
    if out:
        out.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in items), encoding="utf-8")
        typer.echo(f"wrote {len(items)} items -> {out}")
    else:
        _echo(items)


@dataset_app.command("ingest")
def dataset_ingest(path: Path, near_dup_threshold: float = 0.9):
    """수집: 게이트 → 가명화 → 중복제거 → 검수 큐(pending) 적재."""
    from app.api.records import IngestRequest, ingest

    with _session() as db:
        _echo(ingest(IngestRequest(records=_read_jsonl(path),
                                   near_dup_threshold=near_dup_threshold), db))


@dataset_app.command("queue")
def dataset_queue(state: str = "pending"):
    """검수 큐 조회."""
    from app.api.records import queue

    with _session() as db:
        _echo(queue(db, state))


@dataset_app.command("review")
def dataset_review(record_id: str, action: str = typer.Option(...), reviewer: str = typer.Option(...)):
    """승인/반려 (반려 시 증강본 연쇄 폐기)."""
    from app.api.records import ReviewRequest, review

    with _session() as db:
        _echo(review(record_id, ReviewRequest(action=action, reviewer=reviewer), db))


@dataset_app.command("collect-dir")
def dataset_collect_dir(path: Path, pattern: str = "*.jsonl",
                        source_format: str = "canonical",
                        task_type: str = "alert_triage", dataset_version: str = "v0.1.0"):
    """디렉토리 일괄 수집 → 게이트 → 검수 큐 (wise-FP 모드 B)."""
    from app.api.records import IngestRequest, ingest
    from app.services.collect import collect_dir

    records, reports = collect_dir(str(path), pattern, source_format,
                                   {"task_type": task_type, "dataset_version": dataset_version,
                                    "source_type": "dir_collect", "trust_tier": "T2_internal"})
    if not records:
        _echo({"files": reports})
        raise typer.Exit(1)
    with _session() as db:
        _echo({"files": reports, "ingest": ingest(IngestRequest(records=records), db)})


@dataset_app.command("collect-url")
def dataset_collect_url(url: str, source_format: str = "canonical",
                        task_type: str = "alert_triage", dataset_version: str = "v0.1.0"):
    """인터넷 수집 (화이트리스트+사설 IP 차단, T3_untrusted) — wise-FP 모드 C."""
    from app.api.records import IngestRequest, ingest
    from app.services.collect import collect_url

    try:
        records = collect_url(url, source_format,
                              {"task_type": task_type, "dataset_version": dataset_version})
    except ValueError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    with _session() as db:
        _echo({"url": url, "ingest": ingest(IngestRequest(records=records), db)})


@dataset_app.command("augment")
def dataset_augment(substitutions: str = typer.Option(..., help='JSON: {"아파치":"nginx"}')):
    """승인 원본 키워드 치환 증강 → 검수 큐 재편입 (PRD §7.4)."""
    from app.api.records import AugmentRequest, augment

    with _session() as db:
        _echo(augment(AugmentRequest(substitutions=json.loads(substitutions)), db))


# --- models ---

@models_app.command("seed")
def models_seed(profile: str = "pilot"):
    """카탈로그 시드 등록 (pilot/core/all, 멱등)."""
    from app.services.hf_registry import seed_catalog

    with _session() as db:
        _echo(seed_catalog(db, profile))


@models_app.command("list")
def models_list(status: str | None = None, tier: str | None = None):
    """레지스트리 목록."""
    from app.api.registry import list_models

    with _session() as db:
        _echo(list_models(db, status, tier))


@models_app.command("pin")
def models_pin(model_id: str, revision: str = typer.Option(..., help="HF 커밋 해시")):
    """revision 고정 (에어갭 반입 근거)."""
    from sqlalchemy import select

    from app.models.registry import ModelRow

    with _session() as db:
        row = db.scalar(select(ModelRow).where(ModelRow.model_id == model_id))
        if not row:
            typer.echo(f"model not registered: {model_id}", err=True)
            raise typer.Exit(1)
        row.revision, row.status = revision, "pinned"
        db.commit()
        _echo({"model_id": model_id, "status": "pinned", "revision": revision})


@models_app.command("manifest")
def models_manifest():
    """pinned 모델 manifest 출력."""
    from app.services.hf_registry import build_manifest

    with _session() as db:
        _echo(build_manifest(db))


@models_app.command("scan")
def models_scan(path: Path, criteria: str | None = None):
    """신규 모델 이벤트 스캔 (JSONL: {"model_id": ...}) → 유사판정 → candidate 등록."""
    from app.services.hf_registry import register_discovered

    crit = [c.strip() for c in (criteria or settings.hf_similarity_criteria).split(",") if c.strip()]
    with _session() as db:
        _echo(register_discovered(db, _read_jsonl(path), crit))


@models_app.command("download-plan")
def models_download_plan(model_id: str):
    """hf CLI 다운로드 명령 생성 (실행하지 않음)."""
    from sqlalchemy import select

    from app.models.registry import ModelRow
    from app.services.hf_registry import download_plan

    with _session() as db:
        row = db.scalar(select(ModelRow).where(ModelRow.model_id == model_id))
        if not row:
            typer.echo(f"model not registered: {model_id}", err=True)
            raise typer.Exit(1)
        typer.echo(download_plan(row))


# --- tune ---

@tune_app.command("create")
def tune_create(model_id: str, dataset_version: str = typer.Option(...)):
    """튜닝 잡 생성 (approved 레코드 필요)."""
    from app.services.tuning import create_job

    with _session() as db:
        try:
            job = create_job(db, model_id, dataset_version)
        except ValueError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(1) from exc
        _echo({"job_id": job.job_id, "status": job.status, "record_count": job.record_count})


@tune_app.command("plan")
def tune_plan(job_id: str):
    """QLoRA 학습 플랜(YAML) 출력 — worker(GPU) 실행용."""
    from sqlalchemy import select

    from app.models.tuning import TuningJobRow
    from app.services.tuning import train_plan

    with _session() as db:
        job = db.scalar(select(TuningJobRow).where(TuningJobRow.job_id == job_id))
        if not job:
            typer.echo(f"job not found: {job_id}", err=True)
            raise typer.Exit(1)
        typer.echo(train_plan(job))


@tune_app.command("complete")
def tune_complete(job_id: str, status: str = typer.Option(...),
                  adapter_uri: str | None = None, metrics: str | None = None):
    """worker 콜백: 잡 종료 + 지표 리더보드 반영. metrics=JSON 문자열."""
    from app.services.tuning import complete_job

    with _session() as db:
        job = complete_job(db, job_id, status, adapter_uri,
                           json.loads(metrics) if metrics else None)
        _echo({"job_id": job.job_id, "status": job.status})


@tune_app.command("evaluate")
def tune_evaluate(path: Path, model_id: str = typer.Option(...),
                  dataset_version: str = typer.Option(...), job_id: str | None = None):
    """예측 JSONL(expected/prediction) 평가 → 리더보드 반영."""
    from app.services.evaluate import evaluate_predictions
    from app.services.tuning import record_eval

    metrics = evaluate_predictions(_read_jsonl(path))
    with _session() as db:
        record_eval(db, model_id, dataset_version, metrics, job_id=job_id)
    _echo(metrics)


@tune_app.command("leaderboard")
def tune_leaderboard(dataset_version: str | None = None, sort_by: str = "attack_f1"):
    """모델 간 평가 비교 리더보드."""
    from app.services.tuning import leaderboard

    with _session() as db:
        _echo(leaderboard(db, dataset_version, sort_by))


# --- batch ---

@batch_app.command("run")
def batch_run(mode: str | None = None):
    """야간 배치 1회 실행 (트리거 판정 → 스냅샷 → pinned 모델별 잡 생성)."""
    from app.services.batch import run_batch

    with _session() as db:
        _echo(run_batch(db, mode))


@batch_app.command("gate")
def batch_gate(model_id: str, dataset_version: str = typer.Option(...)):
    """배포 게이트 판정 — 미통과 시 exit 1 (스크립트에서 배포 차단)."""
    from app.services.batch import evaluation_gate

    with _session() as db:
        verdict = evaluation_gate(db, model_id, dataset_version)
    _echo(verdict)
    raise typer.Exit(0 if verdict["passed"] else 1)


@batch_app.command("cron-plan")
def batch_cron_plan(base_url: str = "http://127.0.0.1:8000"):
    """야간 배치·HF polling crontab 라인 생성 (실행/설치 없음 — `crontab -e` 로 직접 반영)."""
    from app.services.ops_cron import cron_plan

    typer.echo(cron_plan(base_url))


@batch_app.command("runs")
def batch_runs():
    """배치 실행 이력."""
    from sqlalchemy import select

    from app.services.batch import BatchRunRow

    with _session() as db:
        rows = db.scalars(select(BatchRunRow).order_by(BatchRunRow.id.desc())).all()
        _echo([{"run_id": r.run_id, "status": r.status, "trigger_mode": r.trigger_mode,
                "dataset_version": r.dataset_version, "jobs": r.jobs} for r in rows])


if __name__ == "__main__":
    app()
