# impl/15th 시험 결과 — 수집 채널 확장

- 일시: 2026-08-13
- 판정: **PASS** (pytest 73/73 — 신규 7, ruff clean, 빌드 10라우트, multipart E2E queued=1)

| # | 케이스 | 결과 |
|---|---|---|
| 1~4 | collect 서비스 (파싱·정규화·디렉토리·URL 가드) | PASS |
| 5~6 | upload/collect API | PASS |
| 7 | CLI collect-dir/collect-url | PASS |
| 8 | 프론트 채널 UI + 프록시 업로드 E2E | PASS |
| 9 | 회귀 | PASS |

## 수정·재시험 이력

1. `test_collect_url...` FAIL — 기대값 오류: 레코드 자체 metadata(source_type)가 기본값보다
   우선하는 설계가 정답 → 명시값 우선/미지정 기본값 두 경로 모두 검증하도록 테스트 보강.

## 설계 (PRD §7.3 수집 채널, wise-FP Stage5 Collector 준용)

- **A 파일(멀티)**: `POST /records/upload` (multipart, python-multipart 추가) — JSONL/JSON,
  F6 포맷(alpaca/sharegpt/openai-chat) 자동 변환, 파일별 부분 실패 리포트.
- **B 디렉토리**: `POST /records/collect/dir` — 서버 경로 glob(pattern). PDF/DOCX/CSV 파싱은
  확장 지점(wise-FP _EXT_MAP 상당).
- **C 인터넷**: `POST /records/collect/url` — wise-FP 화이트리스트 도메인 준용 + **SSRF 방지**
  (http/https 만, 사설/루프백/링크로컬/예약 IP 차단), 10MB 상한, `trust_tier=T3_untrusted` 태깅,
  fetcher 주입 가능(오프라인 테스트).
- 공통: record_id 미지정 시 내용 해시 자동, 모든 채널이 기존 ingest 게이트(가명화·중복제거·검수 큐)
  를 그대로 통과 — 게이트 무우회 원칙.
- 프론트: /datasets 수집 채널 섹션(멀티 파일·디렉토리·URL) + 위저드 ②단계 파일 업로드(성공 시 자동 다음).
- CLI: `dataset collect-dir <path> --pattern`, `dataset collect-url <url>`.
