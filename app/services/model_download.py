"""secuftpl — 모델 다운로드 워커 (PRD F2 모델 상태, wise-FP download 준용).

registered → downloading → downloaded. 실 다운로드는 worker(hf CLI, download_plan) —
코어는 상태 전환 + 로컬 스냅샷 매니페스트 생성(시뮬). hf CLI 설치 시 실 다운로드로 확장.
"""
import json
import time
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select

from app.core import db as core_db
from app.models.registry import ModelRow

MODEL_ROOT = Path("./security-llm-models")


def run_download(model_id: str) -> None:
    """백그라운드 다운로드 — 자체 세션."""
    db = core_db.SessionLocal()
    try:
        row = db.scalar(select(ModelRow).where(ModelRow.model_id == model_id))
        if not row or row.status != "downloading":
            return
        time.sleep(0.1)  # 반입 진행감 (실 다운로드 대체)
        safe_name = model_id.replace("/", "__")
        local_dir = MODEL_ROOT / safe_name
        local_dir.mkdir(parents=True, exist_ok=True)
        (local_dir / "snapshot_manifest.json").write_text(json.dumps({
            "model_id": model_id, "family": row.family, "param_size_b": row.param_size_b,
            "tier": row.tier, "role": row.role, "downloaded_at": datetime.now(UTC).isoformat(),
            "mode": "simulate", "note": "실 다운로드는 worker(hf CLI) — 여기서는 스냅샷 매니페스트만",
        }, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        row = db.scalar(select(ModelRow).where(ModelRow.model_id == model_id))
        row.status = "downloaded"
        db.commit()
    except Exception:  # noqa: BLE001 — 실패 시 registered 로 복원
        db.rollback()
        row = db.scalar(select(ModelRow).where(ModelRow.model_id == model_id))
        if row and row.status == "downloading":
            row.status = "registered"
            db.commit()
    finally:
        db.close()
