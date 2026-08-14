"""secuftpl — 데이터셋 다운로드(export) 서비스 (PRD F13 §7.15).

구성된 데이터셋(canonical payload)을 F6 어댑터로 변환해 JSONL 직렬화하고,
출처(F14) 집계·sha256 을 담은 manifest 를 생성한다. 전문가 검증·에어갭 반입 증빙 겸용.
"""
import hashlib
import io
import json
import zipfile
from datetime import UTC, datetime

from app.services.formats import EXPORTERS, convert

EXPORT_FORMATS = ("canonical", "dpo-pairs", *sorted(EXPORTERS))


def filter_by_version(payloads: list[dict], dataset_version: str | None) -> list[dict]:
    """payload 목록 필터 — dataset_version 일치(미지정 시 전체). review_state 는 DB 쿼리에서 처리."""
    if not dataset_version:
        return payloads
    return [p for p in payloads
            if (p.get("metadata") or {}).get("dataset_version") == dataset_version]


def to_jsonl(records: list[dict], target_format: str) -> bytes:
    """canonical 레코드 → target 포맷 JSONL bytes."""
    items = convert(records, "canonical", target_format) if target_format != "canonical" else records
    lines = "\n".join(json.dumps(i, ensure_ascii=False) for i in items)
    return (lines + "\n").encode("utf-8") if lines else b""


def build_manifest(records: list[dict], target_format: str, dataset_version: str | None,
                   review_state: str, jsonl_bytes: bytes) -> dict:
    """export manifest (F13) — 분포·출처별 집계(F14)·파일 sha256."""
    dist: dict[str, dict[str, int]] = {"task_type": {}, "quality_grade": {}, "source_type": {}}
    sources: dict[str, dict] = {}
    for r in records:
        meta = r.get("metadata") or {}
        for key, counter in dist.items():
            val = str(meta.get(key))
            counter[val] = counter.get(val, 0) + 1
        uri = meta.get("source_uri") or "(missing)"
        entry = sources.setdefault(uri, {"count": 0, "license": meta.get("license"),
                                         "source_hash_sha256": meta.get("source_hash_sha256")})
        entry["count"] += 1
    return {
        "dataset_version": dataset_version or "(all)",
        "review_state": review_state,
        "format": target_format,
        "record_count": len(records),
        "distribution": dist,
        "sources": sources,
        "file_sha256": hashlib.sha256(jsonl_bytes).hexdigest(),
        "generated_at": datetime.now(UTC).isoformat(),
    }


def build_zip(jsonl_bytes: bytes, manifest: dict, target_format: str) -> bytes:
    """dataset.jsonl + manifest.json zip 패키징 (with_manifest=true)."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"dataset.{target_format}.jsonl", jsonl_bytes)
        zf.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
    return buf.getvalue()
