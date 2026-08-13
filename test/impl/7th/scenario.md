# impl/7th 시험 시나리오 — E4: 데이터 증강

| # | 케이스 | 방법 | 기대 |
|---|---|---|---|
| 1 | 단어 경계 치환 | `test_substitute_word_boundary` | 부분 문자열 미치환 (아파치캠프 보존) |
| 2 | 보호 식별자 거부 | `test_protected_identifiers_rejected` | CVE/ATT&CK/CWE 치환 사전 → ValueError |
| 3 | lineage·grade | `test_augment_record_lineage_and_grade` | `-aug-N` id, lineage_of, augmented grade, 라벨 불변, 무변화=None |
| 4 | API 흐름 | `test_augment_api_flow_and_reject_cascade` | 승인 원본만 증강→큐 재편입, 무대상 422 |
| 5 | 재증강 금지 | `test_augmented_not_re_augmented` | 증강본(lineage_of≠null) 제외 |
