"""secuftpl — 평가지표 가이드·추천 (PRD F12, E11).

task_type·표본 규모 기반 추천 평가지표 세트 + 가이드 문구. 지표 정의 자체는
app/services/evaluate.py 재사용(신규 지표 계산 없음, 가이드/추천 로직만).
"""

METRIC_GUIDE: dict[str, str] = {
    "json_valid_rate": "구조화 출력(JSON) 파싱 성공 비율 — 다운스트림 자동화 연동의 최소 전제.",
    "severity_accuracy": "severity(심각도) 필드 정확 일치율 — 트리아지/우선순위 판단 품질.",
    "exact_match_rate": "예측이 정답과 완전 일치하는 비율 — 가장 엄격한 지표, 필드가 많을수록 낮게 나옴.",
    "attack_precision": "예측 ATT&CK 기법 중 정답과 일치하는 비율(오탐률의 역).",
    "attack_recall": "정답 ATT&CK 기법 중 예측이 맞춘 비율(누락률의 역).",
    "attack_f1": "attack_precision·recall 조화평균 — ATT&CK 매핑 품질 종합 지표(리더보드 기본 정렬).",
}

# task_type 별 추천 지표 세트 (우선순위 순) — collect.py TASK_PROMPTS 와 동일 task_type 사용
TASK_TYPE_RECOMMENDATIONS: dict[str, list[str]] = {
    "alert_triage": ["severity_accuracy", "attack_f1", "json_valid_rate"],
    "cti_extraction": ["attack_f1", "attack_precision", "attack_recall", "json_valid_rate"],
    "vuln_triage": ["severity_accuracy", "json_valid_rate", "exact_match_rate"],
    "policy_qa": ["exact_match_rate", "json_valid_rate"],
    "safety_refusal": ["exact_match_rate", "json_valid_rate"],
}
DEFAULT_RECOMMENDATION = ["json_valid_rate", "attack_f1", "severity_accuracy"]

# 표본 규모별 신뢰도 안내 (오름차순 상한, 통계적 유의성 참고용 — 하한 없는 안내이지 통계 검정 아님)
_CASE_COUNT_GUIDE: list[tuple[float, str]] = [
    (30, "표본이 30건 미만 — 지표 변동폭이 커 참고용으로만 사용 권장."),
    (100, "표본 30~100건 — 추세 판단 가능, 배포 결정은 100건 이상 권장."),
    (float("inf"), "표본 100건 이상 — 배포 게이트 판단에 사용 가능."),
]


def recommend_metrics(task_type: str, case_count: int | None = None) -> dict:
    """task_type·표본 규모 기반 추천 평가지표 세트 + 가이드 문구(F12)."""
    metrics = TASK_TYPE_RECOMMENDATIONS.get(task_type, DEFAULT_RECOMMENDATION)
    reliability_note = None
    if case_count is not None:
        reliability_note = next(note for limit, note in _CASE_COUNT_GUIDE if case_count < limit)
    return {
        "task_type": task_type,
        "recommended_metrics": metrics,
        "guide": {m: METRIC_GUIDE[m] for m in metrics},
        "case_count": case_count,
        "reliability_note": reliability_note,
        "all_metrics": METRIC_GUIDE,
    }
