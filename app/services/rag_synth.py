"""secuftpl — RAG 코퍼스 → 합성 QA 데이터 (PRD F10·§7.13, E10).

문서/텍스트를 청킹 → cause/resolution 합성 canonical 레코드 생성.
LLM 백엔드(Ollama) 가용 시 실 합성, 미가용 시 결정적 규칙 기반 합성(청크 균등 분할) —
학습 워커(app/services/trainer.py)의 real/simulate 원칙과 동일.
합성 레코드도 §7.3 정제 게이트·검수를 동일 통과해야 데이터셋에 편입된다(게이트 무우회 금지).
"""
import hashlib
import json
from collections.abc import Callable

from app.services.collect import TASK_PROMPTS, extract_document_text

Synthesizer = Callable[[str, str], dict]  # (chunk_text, task_type) -> {"cause":..., "resolution":...}


def chunk_text(text: str, chunk_size: int = 800) -> list[str]:
    """단순 고정 길이 청킹(오버랩 없음) — RAG 임베딩/검색은 Out of Scope, 학습데이터 합성용."""
    text = text.strip()
    if not text:
        return []
    return [c for i in range(0, len(text), chunk_size)
            if (c := text[i:i + chunk_size].strip())]


def _deterministic_synthesize(chunk: str, task_type: str) -> dict:
    """LLM 미가용 시 결정적 대체 — 청크를 원인/해결방안으로 균등 분할."""
    mid = max(1, len(chunk) // 2)
    cause, resolution = chunk[:mid].strip(), chunk[mid:].strip()
    return {"cause": cause, "resolution": resolution or cause}


def ollama_synthesizer(base_url: str, model: str = "qwen2.5:7b-instruct") -> Synthesizer:
    """Ollama 기반 실 합성 — cause/resolution JSON 생성. 미기동 시 OSError(호출측이 폴백 처리)."""
    import urllib.request

    def synth(chunk: str, task_type: str) -> dict:
        prompt = (
            f"{TASK_PROMPTS.get(task_type, TASK_PROMPTS['alert_triage'])}\n\n"
            '다음 문서에서 원인(cause)과 해결방안(resolution)을 '
            '{"cause":"...","resolution":"..."} JSON 형식으로만 출력하라.\n\n' + chunk
        )
        req = urllib.request.Request(
            f"{base_url.rstrip('/')}/api/generate",
            data=json.dumps({"model": model, "prompt": prompt, "stream": False,
                             "format": "json"}).encode(),
            headers={"content-type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as res:
            raw = json.loads(res.read())["response"]
        parsed = json.loads(raw)
        return {"cause": parsed.get("cause", ""), "resolution": parsed.get("resolution", "")}

    return synth


def synthesize_records(chunks: list[str], task_type: str, dataset_version: str,
                       source_uri: str, synthesizer: Synthesizer | None = None) -> list[dict]:
    """청크 목록 → canonical 합성 레코드(F10). source_type=rag_synthesis, quality_grade=augmented,
    canonical 도메인 스키마(§7.2: cause/resolution/unknowns/citations) 준용."""
    synth = synthesizer or _deterministic_synthesize
    prompt = TASK_PROMPTS.get(task_type, TASK_PROMPTS["alert_triage"])
    out = []
    for i, chunk in enumerate(chunks):
        qa = synth(chunk, task_type)
        answer = {"cause": qa.get("cause", ""), "resolution": qa.get("resolution", ""),
                  "unknowns": [], "citations": [source_uri]}
        digest = hashlib.sha256(f"{source_uri}:{i}:{chunk}".encode()).hexdigest()[:16]
        out.append({
            "messages": [
                {"role": "user", "content": f"{prompt}\n\n[RAG 코퍼스: {source_uri}]\n{chunk}"},
                {"role": "assistant", "content": json.dumps(answer, ensure_ascii=False)},
            ],
            "metadata": {
                "record_id": f"rag-{digest}", "source_type": "rag_synthesis",
                "task_type": task_type, "dataset_version": dataset_version,
                "quality_grade": "augmented", "source_uri": source_uri,
                "trust_tier": "T2_internal",
            },
        })
    return out


def synthesize_from_document(data: bytes, filename: str, task_type: str, dataset_version: str,
                             chunk_size: int = 800,
                             synthesizer: Synthesizer | None = None) -> list[dict]:
    """문서 파일(PDF/DOCX/TXT/MD/HTML, F3 채널 재사용) → 합성 레코드."""
    text = extract_document_text(data, filename)
    chunks = chunk_text(text, chunk_size)
    if not chunks:
        raise ValueError(f"no extractable text: {filename}")
    return synthesize_records(chunks, task_type, dataset_version, filename, synthesizer)
