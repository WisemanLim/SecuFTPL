"""secuftpl — 평가 러너 (PRD §5 지표, E3).

지표 근거: .docs/security_sft_dataset_tools.py evaluate — json 유효율·severity 정확도·
exact match·ATT&CK 매핑 P/R/F1. 입력: [{"expected": {...}, "prediction": {...} | "json문자열"}].
"""
import json


def set_f1(pred: list, gold: list) -> tuple[float, float, float]:
    pred_s, gold_s = set(pred), set(gold)
    tp = len(pred_s & gold_s)
    precision = tp / len(pred_s) if pred_s else (1.0 if not gold_s else 0.0)
    recall = tp / len(gold_s) if gold_s else (1.0 if not pred_s else 0.0)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return precision, recall, f1


def evaluate_predictions(rows: list[dict]) -> dict:
    """예측 배치 → 리더보드 지표. prediction 이 문자열이면 JSON 파싱(실패=json_valid 0)."""
    json_valid, severity_ok, exact, scores, value_acc = [], [], [], [], []
    for item in rows:
        expected = item.get("expected", {})
        prediction = item.get("prediction", {})
        if isinstance(prediction, str):
            try:
                prediction = json.loads(prediction)
                json_valid.append(1)
            except json.JSONDecodeError:
                prediction = {}
                json_valid.append(0)
        else:
            json_valid.append(int(isinstance(prediction, dict)))
        scores.append(set_f1(prediction.get("attack_ids", []), expected.get("attack_ids", [])))
        severity_ok.append(int(prediction.get("severity") == expected.get("severity")))
        exact.append(int(prediction == expected))
        value_acc.append(value_accuracy(prediction, expected))
    n = len(rows) or 1
    return {
        "cases": len(rows),
        "json_valid_rate": sum(json_valid) / n,
        "severity_accuracy": sum(severity_ok) / n,
        "exact_match_rate": sum(exact) / n,
        "attack_precision": sum(s[0] for s in scores) / n,
        "attack_recall": sum(s[1] for s in scores) / n,
        "attack_f1": sum(s[2] for s in scores) / n,
        "value_accuracy": sum(value_acc) / n,
    }


def value_accuracy(prediction: dict, expected: dict) -> float:
    """구조화 출력 2축 평가의 값 축 (PRD F16, Survey §2.5) — 스키마 유효성(json_valid)과 별개로
    expected 의 각 필드 값이 실제로 맞았는지 비율. 리스트는 순서 무시 집합 비교."""
    if not expected:
        return 1.0 if not prediction else 0.0
    ok = 0
    for key, want in expected.items():
        got = prediction.get(key)
        if isinstance(want, list) and isinstance(got, list):
            ok += int(sorted(map(str, got)) == sorted(map(str, want)))
        else:
            ok += int(got == want)
    return ok / len(expected)
