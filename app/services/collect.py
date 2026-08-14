"""secuftpl — 데이터셋 수집 채널 (PRD §7.3 수집 채널, wise-FP Stage5 Collector A/B/C 준용).

A. 파일(멀티) 업로드 — JSONL/JSON, F6 포맷 자동 변환(alpaca/sharegpt/openai-chat → canonical)
B. 디렉토리 — 서버 로컬 경로 glob 일괄 수집
C. 인터넷(URL) — 도메인 화이트리스트 + 사설 IP 차단(SSRF 방지), JSON/JSONL 응답만, T3_untrusted

모든 채널은 동일 정제 게이트를 통과한다(게이트 무우회 원칙). PDF/DOCX/CSV 파싱은 확장 지점.
"""
import hashlib
import ipaddress
import json
import socket
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from app.services.formats import convert

# wise-FP _WHITELIST_DOMAINS 준용 (운영에서는 DB/env 관리로 확장)
URL_WHITELIST: frozenset[str] = frozenset([
    "namu.wiki", "ko.wikipedia.org", "en.wikipedia.org",
    "arxiv.org", "pubmed.ncbi.nlm.nih.gov",
    "aihub.or.kr", "data.go.kr", "kostat.go.kr",
    "github.com", "raw.githubusercontent.com", "huggingface.co",
])
MAX_URL_BYTES = 10 * 1024 * 1024  # 10MB 상한


STRUCTURED_EXTS = {".jsonl", ".json"}
DOCUMENT_EXTS = {".pdf", ".docx", ".txt", ".md", ".html", ".htm"}
MAX_DOC_CHARS = 8000  # 문서 본문 상한 (컨텍스트·게이트 비용)

# 문서 수집 시 task별 지시 프레임 (문서 §목표 분리 표 — 정답은 검수 단계에서 작성)
TASK_PROMPTS: dict[str, str] = {
    "alert_triage": "다음 문서의 경보/사고 정보를 분석해 심각도와 대응 절차를 판정하라.",
    "cti_extraction": "다음 위협 보고서에서 ATT&CK 기술과 IOC 를 구조화하라.",
    "vuln_triage": "다음 취약점 보고서를 분석해 대응 우선순위와 완화책을 판정하라.",
    "policy_qa": "다음 정책 문서를 근거로 인용 답변 기준을 정리하라.",
    "safety_refusal": "다음 문서에서 안전 경계(거부·제한 응답) 기준을 도출하라.",
}
NEEDS_ANNOTATION = json.dumps(
    {"status": "needs_annotation", "note": "문서 수집 레코드 — 검수 단계에서 정답(assistant) 작성 필요"},
    ensure_ascii=False,
)


def parse_payload(text: str, filename: str = "upload.jsonl") -> list[dict]:
    """JSONL 또는 JSON(배열/단일 객체) 텍스트 → dict 목록."""
    suffix = Path(filename).suffix.lower()
    if suffix == ".json":
        data = json.loads(text)
        return data if isinstance(data, list) else [data]
    # 기본 JSONL
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def _strip_html(text: str) -> str:
    from html.parser import HTMLParser

    class _T(HTMLParser):
        def __init__(self):
            super().__init__()
            self.parts: list[str] = []
            self._skip = 0

        def handle_starttag(self, tag, attrs):
            if tag in ("script", "style"):
                self._skip += 1

        def handle_endtag(self, tag):
            if tag in ("script", "style") and self._skip:
                self._skip -= 1

        def handle_data(self, data):
            if not self._skip and data.strip():
                self.parts.append(data.strip())

    p = _T()
    p.feed(text)
    return "\n".join(p.parts)


def extract_document_text(data: bytes, filename: str) -> str:
    """문서 파일 → 본문 텍스트 (PDF/DOCX/TXT/MD/HTML — wise-FP _EXT_MAP 상당)."""
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        import io

        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(data))
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    if suffix == ".docx":
        import io

        from docx import Document

        doc = Document(io.BytesIO(data))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    text = data.decode("utf-8", errors="replace")
    if suffix in (".html", ".htm"):
        return _strip_html(text)
    return text  # .txt / .md


def build_document_record(text: str, filename: str, defaults: dict) -> dict:
    """문서 본문 → 주석 대기(needs_annotation) canonical 레코드.
    정답(assistant)은 검수 단계에서 분석가가 작성 — 문서 §수집 원칙(정답 명확성) 준수."""
    body = text.strip()[:MAX_DOC_CHARS]
    if not body:
        raise ValueError(f"no extractable text: {filename}")
    task_type = defaults.get("task_type", "alert_triage")
    prompt = TASK_PROMPTS.get(task_type, TASK_PROMPTS["alert_triage"])
    record = {
        "messages": [
            {"role": "user", "content": f"{prompt}\n\n[문서: {filename}]\n{body}"},
            {"role": "assistant", "content": NEEDS_ANNOTATION},
        ],
        "metadata": {**defaults, "source_type": defaults.get("source_type", "document_upload"),
                     "quality_grade": "silver"},
    }
    return normalize_records([record], "canonical", defaults)[0]


def stamp_attribution(records: list[dict], source_uri: str, raw: bytes | str) -> list[dict]:
    """출처 필수 스탬핑 (PRD F14 게이트 ③) — 수집 채널이 source_uri·source_hash_sha256 을 자동 명기.
    레코드에 이미 값이 있으면 보존(원출처 우선), 없으면 채널 값으로 채운다."""
    payload = raw.encode("utf-8") if isinstance(raw, str) else raw
    digest = hashlib.sha256(payload).hexdigest()
    for rec in records:
        meta = rec.setdefault("metadata", {})
        meta.setdefault("source_uri", source_uri)
        meta.setdefault("source_hash_sha256", digest)
    return records


def collect_file(data: bytes, filename: str, source_format: str, defaults: dict) -> list[dict]:
    """단일 파일 수집 — 확장자 라우팅: 정형(JSONL/JSON) vs 문서(PDF/DOCX/TXT/MD/HTML)."""
    suffix = Path(filename).suffix.lower()
    source_uri = defaults.get("source_uri") or f"upload://{filename}"
    if suffix in STRUCTURED_EXTS:
        items = parse_payload(data.decode("utf-8"), filename)
        return stamp_attribution(normalize_records(items, source_format, dict(defaults)), source_uri, data)
    if suffix in DOCUMENT_EXTS:
        return stamp_attribution(
            [build_document_record(extract_document_text(data, filename), filename, dict(defaults))],
            source_uri, data)
    raise ValueError(f"unsupported file type: {suffix} (지원: jsonl/json/pdf/docx/txt/md/html)")


def normalize_records(items: list[dict], source_format: str, defaults: dict) -> list[dict]:
    """F6 어댑터로 canonical 변환 + metadata 기본값·record_id 자동 보정."""
    records = convert(items, source_format, "canonical", defaults) if source_format != "canonical" else items
    out = []
    for rec in records:
        meta = {**defaults, **(rec.get("metadata") or {})}
        if not meta.get("record_id"):
            digest = hashlib.sha256(
                json.dumps(rec.get("messages", []), ensure_ascii=False).encode()
            ).hexdigest()[:16]
            meta["record_id"] = f"r-{digest}"
        out.append({**rec, "metadata": meta})
    return out


def collect_dir(path: str, pattern: str = "*.jsonl", source_format: str = "canonical",
                defaults: dict | None = None) -> tuple[list[dict], list[dict]]:
    """디렉토리 glob 일괄 수집 → (records, file_reports)."""
    base = Path(path)
    if not base.is_dir():
        raise ValueError(f"not a directory: {path}")
    records: list[dict] = []
    reports = []
    for file in sorted(base.glob(pattern)):
        if not file.is_file():
            continue
        try:
            recs = collect_file(file.read_bytes(), file.name, source_format,
                                {**(defaults or {}), "source_uri": file.resolve().as_uri()})
            records.extend(recs)
            reports.append({"file": file.name, "records": len(recs), "status": "ok"})
        except ValueError as exc:  # JSONDecodeError·UnicodeDecodeError 포함
            reports.append({"file": file.name, "records": 0, "status": f"error: {exc}"})
    return records, reports


def _assert_url_allowed(url: str) -> None:
    """화이트리스트 도메인 + http(s) + 사설/루프백 IP 차단 (SSRF 방지)."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"scheme not allowed: {parsed.scheme}")
    host = parsed.hostname or ""
    if host not in URL_WHITELIST and not any(host.endswith("." + d) for d in URL_WHITELIST):
        raise ValueError(f"domain not in whitelist: {host}")
    for _, _, _, _, sockaddr in socket.getaddrinfo(host, None):
        ip = ipaddress.ip_address(sockaddr[0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            raise ValueError(f"resolves to non-public address: {ip}")


def collect_url(url: str, source_format: str = "canonical",
                defaults: dict | None = None,
                fetcher=None) -> list[dict]:
    """인터넷 수집 — 격리 원칙: T3_untrusted 태깅, 게이트(주입 탐지 포함) 통과 필수.
    fetcher 주입 가능(테스트/오프라인). 기본 urllib, 10MB 상한."""
    _assert_url_allowed(url)
    if fetcher is None:
        def fetcher(u: str) -> str:
            req = urllib.request.Request(u, headers={"User-Agent": "secuftpl-collector/0.1"})
            with urllib.request.urlopen(req, timeout=30) as res:
                return res.read(MAX_URL_BYTES).decode("utf-8")
    text = fetcher(url)
    filename = Path(urlparse(url).path).name or "download.jsonl"
    merged = {"trust_tier": "T3_untrusted", "source_uri": url, "source_type": "web_collect",
              **(defaults or {})}
    # 수집 정의(URL 응답 유형별 자동 판별): JSON/JSONL=레코드, HTML/TXT/MD=본문 추출→주석 대기 레코드
    suffix = Path(filename).suffix.lower()
    if suffix in STRUCTURED_EXTS or (suffix not in DOCUMENT_EXTS and text.lstrip()[:1] in ("{", "[")):
        items = parse_payload(text, filename if suffix in STRUCTURED_EXTS else "download.jsonl")
        return stamp_attribution(normalize_records(items, source_format, merged), url, text)
    return stamp_attribution([build_document_record(
        _strip_html(text) if text.lstrip().startswith("<") else text, filename or url, merged)], url, text)
