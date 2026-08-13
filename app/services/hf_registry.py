"""secuftpl — HF 모델 레지스트리 서비스 (PRD §7.5, F2).

- 시드 등록: 카탈로그(pilot/core/all) → registered
- 유사 모델 판정: HF_SIMILARITY_CRITERIA(family, param_size, license) — 신규 이벤트 모델을
  기존 등록 모델과 비교, 유사 시 candidate 등록(벤치마크 큐 대상, 채택은 사람이 결정)
- manifest: pinned(revision 고정) 목록 — 에어갭/N2SF 반입 근거 (COMPLIANCE)
- download plan: hf CLI 명령 문자열 생성만 — 실행은 worker/사용자 (네트워크 미수행)

실제 HF Hub polling(주 1회, HF_POLLING_CRON)은 ops 스케줄러가 discovered 목록을 만들어
/api/v1/models/events/scan 으로 주입한다 — 코어는 네트워크 무의존.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.registry import ModelRow
from app.services.catalog import infer_family, infer_param_size_b, load_catalog

# param_size 유사 허용 비율 (기존 대비 ±50%)
PARAM_SIZE_TOLERANCE = 0.5


def seed_catalog(db: Session, profile: str) -> dict:
    """카탈로그 시드 등록 (이미 있는 model_id 는 건너뜀 — 멱등)."""
    existing = {m.model_id for m in db.scalars(select(ModelRow))}
    added = []
    for item in load_catalog(profile):
        if item["model_id"] in existing:
            continue
        db.add(ModelRow(**item, status="registered", source="seed"))
        added.append(item["model_id"])
    db.commit()
    return {"profile": profile, "added": len(added), "skipped": len(load_catalog(profile)) - len(added)}


def _criterion_matches(criterion: str, cand: dict, base: ModelRow) -> bool | None:
    """단일 기준 판정. None = 판정 불가(정보 없음 → 기준에서 제외)."""
    if criterion == "family":
        return cand["family"] == base.family
    if criterion == "param_size":
        if cand["param_size_b"] is None or base.param_size_b is None:
            return None
        low = base.param_size_b * (1 - PARAM_SIZE_TOLERANCE)
        high = base.param_size_b * (1 + PARAM_SIZE_TOLERANCE)
        return low <= cand["param_size_b"] <= high
    if criterion == "license":
        if not cand.get("license") or not base.license:
            return None  # 라이선스 미확인 — 추측 금지
        return cand["license"] == base.license
    return None


def find_similar(db: Session, cand: dict, criteria: list[str]) -> str | None:
    """기존 registered/pinned 모델 중 모든 (판정 가능) 기준을 만족하는 첫 모델 id."""
    bases = db.scalars(select(ModelRow).where(ModelRow.status.in_(["registered", "pinned"]))).all()
    for base in bases:
        verdicts = [_criterion_matches(c, cand, base) for c in criteria]
        applicable = [v for v in verdicts if v is not None]
        if applicable and all(applicable):
            return base.model_id
    return None


def register_discovered(db: Session, discovered: list[dict], criteria: list[str]) -> dict:
    """이벤트 감지 모델 → 유사 판정 → candidate 등록. 비유사/기등록은 스킵."""
    results = []
    for raw in discovered:
        model_id = raw["model_id"]
        if db.scalar(select(ModelRow).where(ModelRow.model_id == model_id)):
            results.append({"model_id": model_id, "status": "skipped_exists"})
            continue
        cand = {
            "model_id": model_id,
            "family": raw.get("family") or infer_family(model_id),
            "param_size_b": raw.get("param_size_b", infer_param_size_b(model_id)),
            "license": raw.get("license"),
        }
        matched = find_similar(db, cand, criteria)
        if not matched:
            results.append({"model_id": model_id, "status": "skipped_not_similar"})
            continue
        db.add(ModelRow(
            model_id=model_id, tier="all", role=raw.get("role", "gen"),
            notes=raw.get("notes", "auto-discovered"), family=cand["family"],
            param_size_b=cand["param_size_b"], license=cand["license"],
            status="candidate", source="event", matched_to=matched,
        ))
        results.append({"model_id": model_id, "status": "candidate", "matched_to": matched})
    db.commit()
    return {"total": len(discovered),
            "candidates": sum(1 for r in results if r["status"] == "candidate"),
            "results": results}


def build_manifest(db: Session) -> dict:
    """revision 고정(pinned) 모델 manifest — 에어갭 반입·재현성 근거."""
    rows = db.scalars(select(ModelRow).where(ModelRow.status == "pinned")
                      .order_by(ModelRow.model_id)).all()
    return {"count": len(rows), "models": [
        {"model_id": r.model_id, "revision": r.revision, "tier": r.tier,
         "role": r.role, "license": r.license} for r in rows
    ]}


def download_plan(row: ModelRow, out_dir: str = "./security-llm-models",
                  max_workers: int = 8) -> str:
    """hf CLI 다운로드 명령 문자열 (스크립트 플래그 준용, GGUF 등 제외). 실행하지 않음."""
    safe_name = row.model_id.replace("/", "__")
    revision = f" --revision {row.revision}" if row.revision else ""
    return (
        f"hf download {row.model_id} --repo-type model"
        f" --local-dir {out_dir}/{safe_name}{revision}"
        f" --max-workers {max_workers}"
        f" --exclude '*.gguf' '*.onnx' '*.tflite' '*original*'"
        " ${HF_TOKEN:+--token \"$HF_TOKEN\"}"
    )
