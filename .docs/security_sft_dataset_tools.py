#!/usr/bin/env python3
"""Security SFT dataset validator, Presidio sanitizer, and prediction evaluator.

Install:
  pip install jsonschema presidio-analyzer presidio-anonymizer spacy
  python -m spacy download en_core_web_lg

Examples:
  python security_sft_dataset_tools.py validate data/train.jsonl --report reports/schema.json
  python security_sft_dataset_tools.py sanitize raw.jsonl clean.jsonl --mapping mappings.json
  python security_sft_dataset_tools.py evaluate predictions.jsonl --report reports/metrics.json
"""
import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from jsonschema import Draft202012Validator

SFT_SCHEMA = {
    "type": "object",
    "required": ["messages"],
    "properties": {
        "messages": {
            "type": "array", "minItems": 2,
            "items": {
                "type": "object",
                "required": ["role", "content"],
                "properties": {
                    "role": {"enum": ["system", "user", "assistant"]},
                    "content": {"type": "string", "minLength": 1}
                },
                "additionalProperties": True
            }
        },
        "metadata": {"type": "object"}
    },
    "additionalProperties": True
}

ATTACK_RE = re.compile(r"^T\d{4}(?:\.\d{3})?$")
CVE_RE = re.compile(r"^CVE-\d{4}-\d{4,}$")
CWE_RE = re.compile(r"^CWE-\d+$")
SECRET_PATTERNS = {
    "API_KEY": re.compile(r"\b(?:sk|rk)-[A-Za-z0-9_-]{20,}\b"),
    "AWS_ACCESS_KEY": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "PRIVATE_KEY": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "JWT": re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
    "SESSION_COOKIE": re.compile(r"(?i)\b(?:sessionid|jsessionid|connect\.sid)=[^\s;]{8,}"),
}
INTERNAL_IP_RE = re.compile(r"\b(?:10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|172\.(?:1[6-9]|2\d|3[0-1])(?:\.\d{1,3}){2})\b")
HOST_RE = re.compile(r"\b[A-Z][A-Z0-9]{1,15}-(?:WS|SRV|DB|APP|VPN)-\d{1,5}\b")
CORP_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@(?:[A-Za-z0-9-]+\.)?(?:internal|local|corp)\b", re.I)


def read_jsonl(path):
    for line_no, raw in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if raw.strip():
            yield line_no, json.loads(raw)


def stable_token(kind, value, mapping):
    key = f"{kind}:{value}"
    if key not in mapping:
        mapping[key] = f"<{kind}_{len([k for k in mapping if k.startswith(kind + ':')]) + 1:04d}>"
    return mapping[key]


def replace_regex(text, pattern, kind, mapping):
    return pattern.sub(lambda m: stable_token(kind, m.group(0), mapping), text)


def build_presidio():
    from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
    analyzer = AnalyzerEngine()
    recognizer = PatternRecognizer(
        supported_entity="SECURITY_SECRET",
        patterns=[Pattern(name, pattern.pattern, 0.95) for name, pattern in SECRET_PATTERNS.items()]
    )
    analyzer.registry.add_recognizer(recognizer)
    return analyzer


def sanitize_text(text, analyzer, mapping):
    from presidio_anonymizer import AnonymizerEngine
    from presidio_anonymizer.entities import OperatorConfig
    text = replace_regex(text, INTERNAL_IP_RE, "INTERNAL_IP", mapping)
    text = replace_regex(text, HOST_RE, "HOST", mapping)
    text = replace_regex(text, CORP_EMAIL_RE, "CORP_EMAIL", mapping)
    results = analyzer.analyze(
        text=text, language="en",
        entities=["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD", "IP_ADDRESS", "SECURITY_SECRET"]
    )
    anonymizer = AnonymizerEngine()
    return anonymizer.anonymize(
        text=text, analyzer_results=results,
        operators={"DEFAULT": OperatorConfig("replace", {"new_value": "<REDACTED>"})}
    ).text


def validate_record(record):
    errors = [e.message for e in Draft202012Validator(SFT_SCHEMA).iter_errors(record)]
    messages = record.get("messages", [])
    roles = [m.get("role") for m in messages if isinstance(m, dict)]
    if not roles or roles[-1] != "assistant":
        errors.append("last message must have assistant role")
    if "user" not in roles:
        errors.append("at least one user message is required")
    text = "\n".join(m.get("content", "") for m in messages if isinstance(m, dict))
    for label, pattern in SECRET_PATTERNS.items():
        if pattern.search(text):
            errors.append(f"potential {label} detected")
    return errors


def command_validate(args):
    invalid, total = [], 0
    for line_no, record in read_jsonl(args.input):
        total += 1
        errors = validate_record(record)
        if errors:
            invalid.append({"line": line_no, "errors": errors})
    report = {"total": total, "valid": total - len(invalid), "invalid": len(invalid), "details": invalid}
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ["total", "valid", "invalid"]}, ensure_ascii=False))
    raise SystemExit(1 if invalid else 0)


def command_sanitize(args):
    analyzer, mapping = build_presidio(), {}
    output = []
    for _, record in read_jsonl(args.input):
        for message in record.get("messages", []):
            if isinstance(message, dict) and isinstance(message.get("content"), str):
                message["content"] = sanitize_text(message["content"], analyzer, mapping)
        output.append(record)
    Path(args.output).write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in output), encoding="utf-8")
    Path(args.mapping).write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"records": len(output), "pseudonyms": len(mapping)}, ensure_ascii=False))


def set_f1(pred, gold):
    pred, gold = set(pred), set(gold)
    tp = len(pred & gold)
    precision = tp / len(pred) if pred else (1.0 if not gold else 0.0)
    recall = tp / len(gold) if gold else (1.0 if not pred else 0.0)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return precision, recall, f1


def command_evaluate(args):
    rows = list(read_jsonl(args.input))
    task_exact, json_valid, attack_scores, severity_correct = [], [], [], []
    for _, item in rows:
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
        attack_scores.append(set_f1(prediction.get("attack_ids", []), expected.get("attack_ids", [])))
        severity_correct.append(int(prediction.get("severity") == expected.get("severity")))
        task_exact.append(int(prediction == expected))
    n = len(rows) or 1
    report = {
        "cases": len(rows),
        "json_valid_rate": sum(json_valid) / n,
        "severity_accuracy": sum(severity_correct) / n,
        "exact_match_rate": sum(task_exact) / n,
        "attack_precision": sum(x[0] for x in attack_scores) / n,
        "attack_recall": sum(x[1] for x in attack_scores) / n,
        "attack_f1": sum(x[2] for x in attack_scores) / n,
    }
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("validate")
    p.add_argument("input"); p.add_argument("--report", default="reports/schema-validation.json"); p.set_defaults(func=command_validate)
    p = sub.add_parser("sanitize")
    p.add_argument("input"); p.add_argument("output"); p.add_argument("--mapping", default="pseudonym-mapping.json"); p.set_defaults(func=command_sanitize)
    p = sub.add_parser("evaluate")
    p.add_argument("input", help="JSONL: expected and prediction objects, with attack_ids and severity")
    p.add_argument("--report", default="reports/evaluation.json"); p.set_defaults(func=command_evaluate)
    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
