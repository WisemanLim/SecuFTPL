# test/ — 시험 표준 (wise-dev-standard / test-runner)

사이클: 시나리오 작성 → 시험 진행 → 오류 시 수정·재시험 → 시험결과 작성.

```
test/
├── dev-env/          # 표준 환경 검증 (1회)
│   ├── scenario.md
│   └── logs/         # 원본 로그 (비커밋)
├── impl/<Nth>/       # 구현 차수마다 /wise-dev-standard:implement 가 생성
└── test_*.py         # pytest 유닛/API 테스트 (tests/ 금지 — test/ 로 통일)
```

- 러너: `uv run pytest` (pyproject `testpaths=["test"]`)
- 도메인 추가 시험(COMPLIANCE.md): RLS 크로스테넌트 누출 차단, OpenAPI 계약,
  감사로그 삭제 증명, 정제 게이트(비밀값/PII 스캐너) 회귀
