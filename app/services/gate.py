"""secuftpl — 정제 게이트 검증부 (PRD §7.3 게이트 ④·⑦).

비밀값/내부자산 탐지 + 도메인 규칙 검증. 패턴 근거: .docs/security_sft_dataset_tools.py.
게이트 미통과 레코드는 학습 투입 금지(COMPLIANCE.md 무우회 원칙).
"""
import re

from pydantic import ValidationError

from app.core.schemas import CanonicalRecord

SECRET_PATTERNS: dict[str, re.Pattern[str]] = {
    "API_KEY": re.compile(r"\b(?:sk|rk)-[A-Za-z0-9_-]{20,}\b"),
    "AWS_ACCESS_KEY": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "PRIVATE_KEY": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "JWT": re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
    "SESSION_COOKIE": re.compile(r"(?i)\b(?:sessionid|jsessionid|connect\.sid)=[^\s;]{8,}"),
}
INTERNAL_IP_RE = re.compile(
    r"\b(?:10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}"
    r"|172\.(?:1[6-9]|2\d|3[0-1])(?:\.\d{1,3}){2})\b"
)
HOST_RE = re.compile(r"\b[A-Z][A-Z0-9]{1,15}-(?:WS|SRV|DB|APP|VPN)-\d{1,5}\b")
CORP_EMAIL_RE = re.compile(
    r"\b[A-Za-z0-9._%+-]+@(?:[A-Za-z0-9-]+\.)?(?:internal|local|corp)\b", re.IGNORECASE
)
ASSET_PATTERNS: dict[str, re.Pattern[str]] = {
    "INTERNAL_IP": INTERNAL_IP_RE,
    "HOST": HOST_RE,
    "CORP_EMAIL": CORP_EMAIL_RE,
}
PROMPT_INJECTION_RE = re.compile(
    r"(?:앞\s*지침.{0,10}무시|시스템\s*프롬프트.{0,10}(?:출력|공개)"
    r"|ignore\s+(?:all\s+)?previous\s+instructions?|reveal\s+(?:the\s+)?system\s+prompt)",
    re.IGNORECASE,
)


def scan_text(text: str) -> list[str]:
    """비밀값·내부자산·프롬프트 주입 탐지 → 위반 라벨 목록."""
    findings = [f"potential {label} detected" for label, p in SECRET_PATTERNS.items() if p.search(text)]
    findings += [f"unmasked {label} detected" for label, p in ASSET_PATTERNS.items() if p.search(text)]
    if PROMPT_INJECTION_RE.search(text):
        findings.append("prompt injection phrase detected")
    return findings


def validate_record(raw: dict) -> list[str]:
    """레코드 한 건 검증 → 오류 목록(빈 목록 = 통과)."""
    try:
        record = CanonicalRecord.model_validate(raw)
    except ValidationError as exc:
        return [f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in exc.errors()]
    text = "\n".join(m.content for m in record.messages)
    return scan_text(text)


def validate_records(raws: list[dict]) -> dict:
    """배치 검증 리포트 (security_sft_dataset_tools.py validate 리포트 형식 준용)."""
    details = []
    for idx, raw in enumerate(raws):
        errors = validate_record(raw)
        if errors:
            details.append({"index": idx, "errors": errors})
    return {
        "total": len(raws),
        "valid": len(raws) - len(details),
        "invalid": len(details),
        "details": details,
    }
