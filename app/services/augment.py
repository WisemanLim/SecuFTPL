"""secuftpl — 데이터 증강 (PRD §7.4, E4).

1차 구현: **키워드/단어 치환**(승인된 치환 사전 기반, 라벨 불변) — 결정적·오프라인.
타언어 변환·패러프레이즈는 LLM 백엔드 필요 — Augmenter 프로토콜로 플러그인 지점만 정의.

규칙(PRD §7.4):
- 증강본 record_id = "<원본>-aug-<n>", metadata.lineage_of = 원본, quality_grade = augmented
- 원본 반려 시 연쇄 폐기(검수 큐 lineage 로직이 처리)
- eval/test 증강 금지 — 호출측(ingest 경로)에서만 사용
- 기술 식별자(CVE/ATT&CK ID/코드) 불변 — 치환 사전에 넣지 않는 것으로 강제(검증 포함)
"""
import re
from collections.abc import Callable
from typing import Protocol

# 치환 금지 패턴 — 라벨·기준 체계 식별자 (사전 키에 포함되면 거부)
PROTECTED_RE = re.compile(r"^(?:CVE-\d{4}-\d{4,}|T\d{4}(?:\.\d{3})?|CWE-\d+)$", re.IGNORECASE)


class Augmenter(Protocol):
    """증강 백엔드 플러그인 지점 (번역·패러프레이즈는 LLM 백엔드로 구현)."""

    def augment(self, text: str) -> str: ...


def validate_substitutions(substitutions: dict[str, str]) -> list[str]:
    """치환 사전 검증 — 기술 식별자 치환 금지."""
    return [k for k in substitutions if PROTECTED_RE.match(k.strip())]


def substitute_text(text: str, substitutions: dict[str, str]) -> str:
    """단어 경계 기준 치환 (긴 키 우선 — 부분 치환 방지)."""
    for src in sorted(substitutions, key=len, reverse=True):
        text = re.sub(rf"(?<![\w가-힣]){re.escape(src)}(?![\w가-힣])", substitutions[src], text)
    return text


def augment_record(record: dict, substitutions: dict[str, str], seq: int = 1) -> dict | None:
    """키워드 치환 증강본 생성. 변화 없으면 None (무의미 증강 배제)."""
    new_messages = [
        {**m, "content": substitute_text(m["content"], substitutions)}
        for m in record["messages"]
    ]
    if all(n["content"] == o["content"] for n, o in zip(new_messages, record["messages"], strict=True)):
        return None
    orig_id = record["metadata"]["record_id"]
    return {
        "messages": new_messages,
        "metadata": {
            **record["metadata"],
            "record_id": f"{orig_id}-aug-{seq}",
            "lineage_of": orig_id,
            "quality_grade": "augmented",
        },
    }


def augment_records(records: list[dict], substitutions: dict[str, str]) -> list[dict]:
    """배치 증강. 치환 사전에 보호 식별자 포함 시 ValueError."""
    protected = validate_substitutions(substitutions)
    if protected:
        raise ValueError(f"protected identifiers cannot be substituted: {protected}")
    out = []
    for record in records:
        aug = augment_record(record, substitutions)
        if aug:
            out.append(aug)
    return out


# --- 치환 후보 자동 추천 (PRD §7.4 — 확정은 도메인 전문가) ---

# 보안 도메인 동의어/유사 개체 사전 — 라벨 불변 스왑 후보 (전문가 검수 전제)
SECURITY_SYNONYMS: dict[str, list[str]] = {
    "아파치": ["nginx", "IIS"], "apache": ["nginx", "IIS"], "nginx": ["아파치", "IIS"],
    "윈도우": ["리눅스", "macOS"], "windows": ["linux", "macos"], "리눅스": ["윈도우", "유닉스"],
    "파워쉘": ["배시", "cmd"], "powershell": ["bash", "cmd"],
    "웹서버": ["애플리케이션 서버", "프록시 서버"], "방화벽": ["IPS", "웹방화벽"],
    "이메일": ["메신저", "협업도구"], "피싱": ["스미싱", "비싱"],
    "워크스테이션": ["서버", "노트북"], "데이터베이스": ["파일서버", "스토리지"],
    "mysql": ["postgresql", "mariadb"], "postgresql": ["mysql", "mariadb"],
}
_STOPWORDS = frozenset(["을", "를", "이", "가", "은", "는", "의", "에", "에서", "으로", "로", "및", "또는", "그리고", "다음", "해당", "대한", "위한", "경우", "the", "a", "an", "of", "to", "in", "for", "and", "or"])
_TOKEN_RE = re.compile(r"[A-Za-z가-힣][A-Za-z0-9가-힣]{1,20}")


def suggest_substitutions(records: list[dict], top_n: int = 10) -> list[dict]:
    """승인 레코드 텍스트에서 빈도 키워드 추출 + 동의어 사전 매칭 → 치환 후보 제안."""
    from collections import Counter

    counter: Counter[str] = Counter()
    for record in records:
        for m in record["messages"]:
            for token in _TOKEN_RE.findall(m["content"]):
                low = token.lower()
                if low in _STOPWORDS or PROTECTED_RE.match(token):
                    continue
                counter[low] += 1
    suggestions = []
    for keyword, freq in counter.most_common():
        if keyword in SECURITY_SYNONYMS:
            suggestions.append({"keyword": keyword, "frequency": freq,
                                "candidates": SECURITY_SYNONYMS[keyword]})
        if len(suggestions) >= top_n:
            break
    return suggestions


# --- 역번역 증강 (PRD §7.4 타언어 변환 — ko→en→ko 표현 변형) ---

Translator = Callable[[str, str, str], str]  # (text, src_lang, tgt_lang) -> text


def _protect_identifiers(text: str) -> tuple[str, dict[str, str]]:
    """번역 전 기술 식별자(CVE/ATT&CK/CWE) 자리표시 보호 → 번역 후 복원."""
    ids = re.findall(r"CVE-\d{4}-\d{4,}|T\d{4}(?:\.\d{3})?|CWE-\d+", text)
    mapping = {}
    for i, ident in enumerate(dict.fromkeys(ids)):
        token = f"__ID{i}__"
        mapping[token] = ident
        text = text.replace(ident, token)
    return text, mapping


def back_translate_record(record: dict, translator: Translator, seq: int = 1) -> dict | None:
    """ko→en→ko 역번역 증강본. 변화 없으면 None. 식별자 불변 보존."""
    new_messages = []
    changed = False
    for m in record["messages"]:
        if m["role"] != "user":  # 정답(assistant)·system 은 라벨/규약 — 변형 금지
            new_messages.append(m)
            continue
        protected, mapping = _protect_identifiers(m["content"])
        translated = translator(translator(protected, "ko", "en"), "en", "ko")
        for token, ident in mapping.items():
            translated = translated.replace(token, ident)
        changed = changed or translated != m["content"]
        new_messages.append({**m, "content": translated})
    if not changed:
        return None
    orig_id = record["metadata"]["record_id"]
    return {"messages": new_messages,
            "metadata": {**record["metadata"], "record_id": f"{orig_id}-bt-{seq}",
                         "lineage_of": orig_id, "quality_grade": "augmented"}}


def back_translate_records(records: list[dict], translator: Translator) -> list[dict]:
    out = []
    for record in records:
        aug = back_translate_record(record, translator)
        if aug:
            out.append(aug)
    return out


def ollama_translator(base_url: str, model: str = "qwen2.5:7b-instruct") -> Translator:
    """Ollama 번역 백엔드 (SERVING_STACK=ollama 연동). 미기동 시 OSError."""
    import json as _json
    import urllib.request

    def translate(text: str, src: str, tgt: str) -> str:
        prompt = (f"Translate the following {src} text to {tgt}. "
                  f"Output ONLY the translation, no explanations.\n\n{text}")
        req = urllib.request.Request(
            f"{base_url.rstrip('/')}/api/generate",
            data=_json.dumps({"model": model, "prompt": prompt, "stream": False}).encode(),
            headers={"content-type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as res:
            return _json.loads(res.read())["response"].strip()

    return translate
