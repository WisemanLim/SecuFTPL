"""가명화(게이트 ⑤)·중복제거(게이트 ⑥) 테스트."""
from app.services.dedup import content_hash, find_near_duplicates, jaccard, shingles
from app.services.sanitize import sanitize_record, sanitize_text


def test_stable_token_consistency():
    mapping: dict[str, str] = {}
    t1 = sanitize_text("host FIN-WS-021 from 192.168.10.5", mapping)
    t2 = sanitize_text("again FIN-WS-021 and 192.168.10.5", mapping)
    assert "<HOST_0001>" in t1 and "<INTERNAL_IP_0001>" in t1
    assert "<HOST_0001>" in t2 and "<INTERNAL_IP_0001>" in t2  # 동일 원문 = 동일 토큰
    t3 = sanitize_text("new host FIN-WS-099", mapping)
    assert "<HOST_0002>" in t3  # 다른 원문 = 순번 증가


def test_secret_replaced_with_token():
    mapping: dict[str, str] = {}
    out = sanitize_text("key AKIAIOSFODNN7EXAMPLE end", mapping)
    assert "AKIA" not in out and "<AWS_ACCESS_KEY_0001>" in out


def test_sanitize_record_immutable():
    rec = {
        "messages": [
            {"role": "user", "content": "ip 10.0.0.1"},
            {"role": "assistant", "content": "ok"},
        ],
        "metadata": {"record_id": "r-1"},
    }
    mapping: dict[str, str] = {}
    clean = sanitize_record(rec, mapping)
    assert "<INTERNAL_IP_0001>" in clean["messages"][0]["content"]
    assert rec["messages"][0]["content"] == "ip 10.0.0.1"  # 원본 불변


def _rec(user, assistant="답변"):
    return {"messages": [{"role": "user", "content": user},
                         {"role": "assistant", "content": assistant}],
            "metadata": {"record_id": "x"}}


def test_content_hash_normalization():
    a = _rec("경보  분석   하라")
    b = _rec("경보 분석 하라")
    assert content_hash(a) == content_hash(b)  # 공백 정규화 후 동일


def test_jaccard_and_shingles():
    s1 = shingles("a b c d e")
    s2 = shingles("a b c d f")
    assert 0 < jaccard(s1, s2) < 1
    assert jaccard(set(), set()) == 1.0


def test_find_near_duplicates():
    records = [
        _rec("파워쉘 인코딩 명령 실행 탐지 경보를 분석하고 심각도를 판정하라"),
        _rec("파워쉘 인코딩 명령 실행 탐지 경보를 분석하고 심각도를 판정해라"),  # 근접
        _rec("완전히 다른 취약점 우선순위 질의"),
    ]
    pairs = find_near_duplicates(records, threshold=0.6)
    assert (0, 1) in [(i, j) for i, j, _ in pairs]
    assert all(2 not in (i, j) for i, j, _ in pairs)
