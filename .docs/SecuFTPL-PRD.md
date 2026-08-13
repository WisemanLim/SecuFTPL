# PRD: SecuFTPL — 보안분야 LLM Fine-Tune Pipeline 플랫폼

> 유형: 풀스펙(One-Page §1~6 + 기술 확장 §7~8) · 업종 오버레이: ict-saas(베이스라인) + govtech + finance
> 근거 문서: `.docs/Perplexity-보안분야 LLM 모델 생성.md`, `.docs/security_sft_dataset_tools.py`,
> `.docs/download_security_llm_models_macos.sh`, wise-FP(Finetuning-Pipeline frontend/worker/ops),
> `.docs/LLM,RAG/Eden-FP No-Code Domain AI Platform.pdf`(F9·F10 리소스/모니터링·RAG 추가학습 근거),
> `.docs/LLM,RAG/*.md`(Ollama/vLLM/llama.cpp/MLX·RAG 조사자료, F10·F11 근거)

## 1. 개요

- **한 줄 요약**: 기존 wise-FP(23세션 제조업 등 범용 Fine-Tune 파이프라인)를 **보안 도메인 전용**으로
  특화한 플랫폼. 보안 데이터셋 구축(수집·정제·증강) → 다중 베이스모델 파인튜닝 → 모델 간 평가 비교 →
  Agent 피드백 루프 → 규모 기반 야간 배치 자동 재튜닝·재배포까지 전 주기를 담당한다.
- **배경 / 왜 지금**: 보안 업무(SOC 경보 분류, CTI 정규화, 취약점 트리아지, 보안 정책 QA)는 범용 LLM으로는
  구조화 출력 유효성·ATT&CK 매핑 정확도·환각 억제가 부족하다. 근거 문서가 제시하듯
  "공개 instruct 모델 + PEFT(QLoRA) 파인튜닝 + 평가 게이트" 조합이 비용·통제·성능 면에서 최적이며,
  wise-FP 자산(frontend/worker/ops)이 이미 있어 도메인 특화 비용이 낮다.
- **작성자 / 날짜 / 버전**: Wiseman Lim / 2026-08-12 (초안) → 2026-08-13 고도화 / v0.2 (F9~F12 추가)

## 2. 문제와 대상 (Why & Who)

- **해결하려는 핵심 문제**:
  1. 보안 도메인 학습 데이터는 "많음"보다 "추적 가능·정답 명확·민감정보 제거"가 관건인데,
     수집→정제→검수→버전관리를 수작업으로 하면 재현성과 규모 확장이 불가능하다.
  2. 베이스모델(Qwen/Llama/Gemma 등)마다 한국어 보안 용어·구조화 출력 성능이 달라
     동일 데이터셋 기준 정량 비교 없이는 모델 선정이 감에 의존한다.
  3. AI Assistant 운영 중 발생하는 질의/답변/만족도가 데이터셋으로 환류되지 않아 모델이 정체된다.
- **비즈니스 관점 중요성**: 보안 특화 모델은 SeCuardian 계열 제품의 핵심 차별화 요소.
  파이프라인 자동화 없이는 신규 모델 출시·신규 위협 대응 속도를 따라갈 수 없다.
- **근거 데이터 / VOC / 로그**: `.docs/Perplexity-보안분야 LLM 모델 생성.md`(파이프라인 설계·학습기법·평가 게이트),
  기존 wise-FP 23세션 운영 경험, `security_sft_dataset_tools.py`(스키마 검증·Presidio 정제·평가 지표 PoC).
- **타깃 사용자 / 페르소나** (4역할):
  | 역할 | 플랫폼에서 하는 일 |
  |---|---|
  | ML/파인튜닝 엔지니어 | 베이스모델 선택, 튜닝 잡 실행, 하이퍼파라미터·어댑터 관리, 평가 비교 |
  | 보안 도메인 전문가 / SOC 분석가 | 원인/해결방안 데이터 검수, 품질 라벨링(gold/silver), 안전 거부 예제 승인 |
  | AI Assistant 최종 사용자 | 질의/답변 사용 + 만족도 피드백 (Agent화 데이터 원천) |
  | 플랫폼 운영자(ops) | 야간 배치 튜닝·재배포·롤백, 모델 레지스트리·모니터링 |
- **대표 사용 상황**: 신규 보안 사고 데이터가 축적됨 → 도메인 전문가가 원인/해결방안 검수 →
  임계 규모 도달 시 야간 배치가 자동 파인튜닝·평가·재배포 → Assistant 응답 품질이 다음 날 개선.

## 3. 범위 (What — In / Out)

### In Scope (P0/P1)

| # | 기능 | 우선순위 | 요구사항 매핑 |
|---|---|---|---|
| F1 | **다중 베이스모델 파인튜닝·모델 간 평가 비교** — 동일 데이터셋으로 N개 베이스모델(Qwen2.5/Llama 3.1/Gemma 3 등) QLoRA SFT 실행, 공통 평가셋으로 리더보드 비교(JSON 유효율·ATT&CK F1·severity accuracy 등) | P0 | 요구 1 |
| F2 | **HuggingFace 모델 관리** — 프로파일(pilot/core/all) 기반 모델 다운로드, revision pin·manifest 생성(에어갭 대비), 신규 모델 이벤트(HF 신규 릴리스/조직 watch) 감지 시 유사 모델 후보 자동 등록·벤치마크 큐 투입 | P0 | 요구 2 |
| F3 | **보안 데이터셋 구축** — 원인/해결방안/만족도 3요소 스키마 기반 수집·정제 파이프라인(§7.3 상세) + 데이터 증강(타언어 변환, 원인/해결방안 내 단어·키워드 치환) | P0 | 요구 3 |
| F4 | **Agent화 피드백 루프** — AI Assistant의 모든 입력/출력(질의/답변)을 만족도 포함 레코드로 수집 → 정제 게이트 통과 후 데이터셋 편입 | P0 | 요구 4 |
| F5 | **파인튜닝 자동화** — 데이터셋 증분 규모 임계값 기반 야간 배치 트리거 → 파인튜닝 → 평가 게이트 → 통과 시 자동 재배포(실패 시 롤백·알림) | P1 | 요구 5 |
| F6 | **다양한 데이터셋 포맷(spec) 지원** — SFT messages JSONL(내부 표준), Alpaca, ShareGPT, OpenAI chat, DPO 선호쌍, 평가셋 포맷 간 변환 어댑터 계층 | P1 | 확장성 요구 |
| F7 | **Supervisor 파이프라인 시험 UI** — wise-FP frontend 준용(로그인 제외): 모델 선택·사용용도(task_type)·데이터셋 선택/입력 → 파이프라인 단계(검증→수집→검수, 향후 튜닝 잡) 시험. 1차=경량 내장 UI, 본편=E7 Next.js 확장 | P1 | 2026-08-13 추가 |
| F8 | **파이프라인 CLI** — frontend 부재 환경에서 각 파이프라인(데이터셋 검증/변환/수집/검수, 모델 시드/pin/manifest/스캔/다운로드플랜) 실행 명령 제공 + **원스톱 오케스트레이션 스크립트**(`scripts/run-pipeline.sh`) — 모델 선택→데이터셋 수집→검수 승인→(증강)→튜닝 잡→평가 게이트→리더보드 비교→배포(export) 전 과정을 한 번에 실행, 백엔드 미기동 시 자동 구동·완료 후 정리 | P1 | 2026-08-13 추가·2026-08-13 확장 |
| F9 | **튜닝 리소스/모니터링 세부설정** — 잡별 GPU/CPU/VRAM/동시성 슬롯 지정, 실시간 리소스 대시보드(GPU util·VRAM·throughput·ETA), wise-FP ops 리소스 매니저 준용, 임계 초과 시 대기열·알림 | P1 | 2026-08-13 추가(Eden-FP 참고) |
| F10 | **RAG 기반 추가학습(모델 업그레이드)** — 베이스모델(+기존 어댑터)에 RAG 코퍼스(문서/벡터DB)로 합성한 QA/지식 데이터를 continual fine-tuning → 신규 모델 버전으로 승격, 기존 평가 게이트·리더보드 동일 적용 | P1 | 2026-08-13 추가 |
| F11 | **다중 런타임 배포·풀모델 export** — 배포 대상(Ollama/vLLM/llama.cpp/MLX) 선택 → 어댑터 merge 후 풀모델(safetensors) 저장, 런타임별 포맷 변환(GGUF/MLX) → 어댑터 외 풀모델 파일 다운로드/서빙 등록 | P0 | 2026-08-13 추가 |
| F12 | **평가지표 가이드·추천** — task_type·데이터셋 특성 기반 추천 평가지표 세트(§5) 제시, 지표 선택 UI에 가이드 문구·기본값 사전 채움 | P1 | 2026-08-13 추가 |

### Out of Scope (이번 릴리즈에서 하지 않을 것)

- 파운데이션 모델 사전학습(pre-training) — 공개 instruct 모델 파인튜닝만 (근거 문서 권고)
- RAG 서비스(질의응답 서빙·벡터DB 운영) 자체 구축 — 플랫폼은 F10처럼 **RAG 코퍼스를 학습데이터로 흡수해
  모델을 업그레이드**하는 것까지만 담당. 런타임 RAG 인덱스 갱신·검색 서빙은 별도 시스템(2026-08-13 명확화)
- 공격 도구·오펜시브 페이로드 생성 기능 — 방어 목적 한정, 안전 거부 데이터로만 취급
- 멀티모달(이미지·PDF 증적) 학습 — 2차 릴리즈 후보
- DPO/ORPO 선호학습 자동화 — SFT 안정화 후 확장 (수동 실행은 worker에서 가능)

## 4. 사용자 경험 (How — User Flow)

- **시나리오 1 (데이터셋 구축→튜닝→비교)**: ML 엔지니어가 frontend에서 수집 소스(사고 티켓/공개 CTI/Assistant 로그)를
  등록 → 정제 게이트(비식별화·중복제거·스키마 검증) 통과 현황 대시보드 확인 → 도메인 전문가가 검수 큐에서
  원인/해결방안 레코드 승인 → 엔지니어가 베이스모델 3종 선택 후 튜닝 잡 제출 → worker가 QLoRA SFT 실행 →
  평가 리더보드에서 모델별 지표 비교 → 승자 모델을 스테이징 배포.
- **시나리오 2 (Agent 환류→야간 자동 튜닝)**: Assistant 사용자가 질의 후 만족도(👍/👎+사유) 입력 →
  레코드가 수집 큐에 적재 → 정제·증강 후 데이터셋 버전 증분 → 야간 배치가 임계값(가정: 신규 승인 레코드 500건)
  도달 확인 → 자동 파인튜닝·평가 게이트 → 통과 시 재배포, ops는 아침에 결과 리포트 확인.
- **시나리오 3 (RAG 추가학습→모델 업그레이드, F10, 2026-08-13 추가)**: 엔지니어가 기존 배포 모델(베이스+어댑터)을
  업그레이드 대상으로 선택 → RAG 코퍼스(문서/벡터DB, F3 수집 채널 재사용)에서 QA/지식 데이터 합성 →
  기존 데이터셋과 병합해 continual fine-tuning 잡 제출 → 리소스 모니터링(F9)으로 진행 확인(다른 메뉴 이동해도
  백그라운드 계속) → 평가 게이트(§5 지표 + 추천 가이드 F12) 통과 시 신규 모델 버전으로 승격 → 배포 단계에서
  런타임(Ollama/vLLM/llama.cpp/MLX) 선택 후 어댑터 또는 풀모델(F11) 다운로드.

> 프론트엔드 포함(SecuFTPL 독립 `frontend/`) — 상세 화면 설계 시 `/wise-dev-standard:ui-design` 으로
> 대시보드·검수 큐·리더보드·리소스 모니터링 UI 레퍼런스를 보강할 것.

## 5. 성공 지표 (Success)

| 분류 | KPI | 기준선(Baseline) | 목표값(Target) | 측정 방법 |
|---|---|---|---|---|
| 모델 평가 | 구조화 출력 JSON 유효율 | 베이스모델 무튜닝 측정치 | ≥ 98% (가정) | `evaluate` 리포트 `json_valid_rate` |
| 모델 평가 | ATT&CK 매핑 F1 | 베이스모델 무튜닝 측정치 | 기준선 대비 +20%p (가정) | `attack_f1` |
| 모델 평가 | severity 분류 정확도 | 베이스모델 무튜닝 측정치 | ≥ 85% (가정) | `severity_accuracy` |
| 만족도 | Assistant 응답 만족(👍) 비율 | 최초 4주 운영치 | 분기별 +5%p (가정) | 피드백 레코드 집계 |
| 자동화 | 야간 배치 튜닝→재배포 무인 성공률 | — (신규) | ≥ 90% (가정) | ops 배치 잡 로그 |
| 데이터셋 | 정제 게이트 통과 승인 레코드 증가량 | — (신규) | 주간 +N건 목표 설정 (가정: 500건/주) | 데이터셋 버전 manifest diff |
| 데이터셋 | 증강 배수(원본 대비) | 1x | 3~5x (가정: 언어변환 2종 + 키워드 치환) | 증강 파이프라인 통계 |
| RAG 업그레이드 | RAG 추가학습 후 평가 지표 개선폭(F10) | 업그레이드 전 모델 평가치 | 회귀 없음 + 대상 지표 개선 (가정) | 업그레이드 전/후 리더보드 diff |
| 배포 | 런타임별 export 성공률(F11: Ollama/vLLM/llama.cpp/MLX) | — (신규) | ≥ 95% (가정) | export 잡 로그 |

> 기준선은 F1 첫 벤치마크(무튜닝 베이스모델 평가)에서 확정한다. 모든 `가정:` 값은 확정 후 갱신.

## 6. 리스크 및 메모

- **주요 리스크**:
  - 학습 데이터 내 민감정보(API 키·내부 IP·고객 PII) 잔존 → 모델이 재현 시 유출 사고 (정제 게이트 P0, §7.3)
  - 외부 CTI/문서 내 프롬프트 주입 문구가 학습 오염 → 수집 격리·주입 탐지 필수
  - HF gated model(Llama 등) 라이선스·배포 조건 — 파생물(어댑터) 배포 가능 여부 모델별 검토
  - 자동 재배포 시 회귀(성능 하락) 모델 배포 → 평가 게이트 미통과 시 배포 차단 + 롤백 필수
  - 증강 데이터 품질 저하(기계 번역·치환 오류) → 증강본 별도 quality_grade, 비율 상한(가정: gold의 50%)
  - GGUF/MLX 등 포맷 변환 시 정밀도 손실(quantization) → 변환 후 스모크 평가(§5 지표 일부) 재실행 필수(F11)
  - RAG 코퍼스 저작권·라이선스 불명 문서가 학습에 흡수됨 → F10도 §7.3 정제 게이트(라이선스·출처 확인) 동일 적용
  - 리소스 세부설정(F9) 과다 할당 시 잡 경합·GPU OOM → 잡 큐잉 + 상한 가드레일(§7.12)
- **의존성**: wise-FP 3컴포넌트(frontend/worker/ops) 재사용·확장, HuggingFace Hub API,
  GPU 자원(야간 배치 슬롯), Presidio+spaCy(비식별화), MITRE ATT&CK/CVE/CWE 데이터(라벨 기준 체계)
- **규제/컴플라이언스 메모** (업종 오버레이):
  - *ict-saas(베이스라인)*: 개인정보보호법(PIPA) — 학습 데이터 PII 최소화·비식별화, ISMS-P 증적(접근로그·변경관리),
    감사로그 보관·삭제 정책(SOC2 CC6.5/ISO A.8.10)
  - *govtech(공공 고객 시)*: N2SF 등급(C/S/O) 망분리 — 에어갭 배포 대비 모델 manifest·revision pin 필수(F2가 충족),
    CSAP 인증 클라우드 요건, 공공 데이터 반출 통제
  - *finance(금융 고객 시)*: 신용정보법 — 개인신용정보 비프로드 반출 금지·가명정보만 R&D 사용 가능(2025 개정),
    전자금융감독규정 위험기반 망분리, append-only 감사로그
- **확정된 운영 옵션 (2026-08-12 결정 — §7.9 환경 설정 반영)**:
  - 야간 배치 트리거: 레코드 수/토큰 수/주기 고정 중 **옵션 설정**, 기본값 **주기 고정**
  - 신규 모델 이벤트 감지: polling/webhook 중 **옵션 설정**, 기본값 **polling·주 1회**.
    유사 모델 판정 기준(파라미터 규모·계열·라이선스)도 옵션화
  - 만족도 스키마: 이진(up/down)·5점 척도(1~5) 모두 저장 가능한 구조, **옵션 설정**, 기본값 **이진 up/down**
  - 모델 서빙 스택: vLLM/Ollama/TGI 중 **옵션 설정**, 기본값 **Ollama**
- **미결정 사항 (Open Questions)**: (현재 없음 — 신규 발생 시 여기에 기록)

---

## 7. 기술 메모 (Technical Notes)

> 이하 구현 방식은 예시/초안이다. 확정은 recommend→scaffold 단계에서.

### 7.1 아키텍처 (wise-FP 확장 — 예시)

```text
[수집 계층]                          [wise-FP 확장 컴포넌트]
 사고티켓/IR │ 공개지식(ATT&CK,CVE)     frontend  : 데이터셋 대시보드·검수 큐·모델 리더보드·잡 제출 UI
 Assistant 질의/답변/만족도(F4)        worker    : 정제·증강·QLoRA SFT·평가 실행 (GPU)
        │                             ops       : 야간 배치 스케줄러·재배포·롤백·모니터링
        ▼
[데이터셋 계층]  수집 격리 → 정제 게이트 → 검수 큐 → 증강 → 버전화(manifest+hash)
        │            (§7.3)                    (§7.4)
        ▼
[학습 계층]      베이스모델 레지스트리(HF 다운로드·revision pin, F2)
                 → QLoRA SFT (N개 모델 병렬, F1) → 어댑터 저장소
        ▼
[평가 계층]      공통 평가셋 → json_valid/attack_f1/severity/exact_match → 리더보드(F1)
        ▼
[배포 계층]      평가 게이트 통과 → 스테이징 → 자동 재배포(F5) → Assistant 서빙
                        └ 미통과: 차단 + ops 알림 + 이전 버전 유지
```

- 핵심 분리 원칙(근거 문서): 파인튜닝은 "행동 양식·출력 규약·판단 기준"만 학습. 최신 CVE/IOC/정책은
  RAG 인덱스 갱신 대상(Out of Scope)이며 매번 재튜닝하지 않는다.
- 릴리스 단위: 데이터 스냅샷 + 어댑터 + 평가 결과를 함께 버전 관리(지속학습 아닌 재학습 릴리스).

### 7.2 데이터셋 포맷 spec (F6 — 확장성)

내부 정규 포맷(canonical)은 **SFT messages JSONL + metadata** (`security_sft_dataset_tools.py` SFT_SCHEMA 준용).
모든 외부 포맷은 canonical과 양방향 변환 어댑터를 거친다.

| spec | 용도 | 변환 방향 |
|---|---|---|
| `sft-messages` (canonical) | 내부 표준. system/user/assistant + metadata | — |
| `alpaca` (instruction/input/output) | 공개 데이터셋 수입 | import/export |
| `sharegpt` (conversations) | 멀티턴 공개 데이터셋 수입 | import/export |
| `openai-chat` | 외부 튜닝 API 호환 export | export |
| `dpo-pairs` (prompt/chosen/rejected) | 선호학습 확장 대비(만족도 👍/👎 쌍에서 생성) | export |
| `eval-set` (expected/prediction) | 평가 러너 입력 | export |

canonical metadata 필수 필드(데이터 계약, 근거 문서 §데이터 계약과 계보):
`record_id, source_type, source_uri, source_hash_sha256, ingested_at, license, trust_tier,
sensitivity, review_state, dataset_version, task_type, language, quality_grade(gold/silver/augmented), reviewer`

**원인/해결방안/만족도 도메인 스키마(요구 3·4)** — canonical의 task별 assistant 출력 형식:

```json
{
  "cause": "탐지된 근본 원인 (근거 문장·로그 필드·문서 ID 인용)",
  "resolution": "해결방안 (단계별, 고위험 조치는 requires_human_approval=true)",
  "unknowns": ["확인 불가 항목"],
  "citations": ["doc_id..."],
  "satisfaction": {"scale": "binary|likert5", "score": "up|down 또는 1~5", "reason_tags": ["부정확","불충분","형식오류"], "rated_by": "user|analyst", "rated_at": "..."}
}
```

### 7.3 수집·정제 파이프라인 (F3·F4 — 면밀 검토 반영)

**수집 소스 우선순위** (근거 문서 §수집 단계):

| 우선순위 | 소스 | 용도 |
|---|---|---|
| P0 | 분석가 확정 Alert/IR 티켓/해결 이력 | 원인/해결방안 gold data |
| P0 | MITRE ATT&CK, CWE, CVE/NVD, CISA KEV | 라벨 기준 체계·정답 검증 |
| P0 | Assistant 질의/답변 + 만족도(F4) | 환류 데이터 (👍=chosen 후보, 👎=검수 큐) |
| P1 | 사내 보안 정책·플레이북, 검증된 벤더 권고문 | 정책 QA 태스크 |
| P2 | 외부 블로그·포럼 | 격리·비신뢰 취급 |
| 금지 | 실운영 비밀, 활성 악성코드, 고객 원문 | 수집 자체 차단 |

**정제 게이트** (전 레코드 통과 필수 — `security_sft_dataset_tools.py` 확장):

```text
Raw → ① 수집 격리 (source_type별 quarantine)
    → ② 프롬프트 주입 문구 탐지 ("앞 지침 무시" 류 → 인용 텍스트 처리 or 차단)
    → ③ 라이선스·출처 확인 (license/source_hash 없는 레코드 반입 금지)
    → ④ 비밀값·PII 탐지: SECRET_PATTERNS(API키/AWS키/개인키/JWT/세션쿠키)
       + 내부IP·호스트명·사내메일 정규식 + Presidio NER(인명/전화/카드/IP)
    → ⑤ 가명화: 삭제 대신 안정 토큰 치환(<INTERNAL_IP_0001>) — 문맥 보존, mapping 별도 보관
    → ⑥ 중복·근접중복 제거 (동일 사고/IOC/보고서의 train-test 누수 방지)
    → ⑦ 스키마 검증 (SFT_SCHEMA + 도메인 규칙: attack_id 실존, citations 없는 단정 fail,
       고위험 조치 requires_human_approval 필수, confidence>0.85 & 단일 evidence → review queue)
    → ⑧ split 분리: 시간·사건 단위 기준 train/valid/test (랜덤 split 금지)
    → ⑨ 사람 검수(도메인 전문가): gold 승인 or 반려 — 승인만 데이터셋 편입
    → ⑩ manifest + sha256 hash 생성, dataset_version 증분
```

- Assistant 환류(F4) 전용 규칙: 만족도 👎 레코드는 자동 편입 금지 — 검수 큐에서 교정 답변 작성 후
  gold로 승격하거나 향후 DPO rejected로 보관. 개인 식별 가능한 질의는 ④~⑤ 게이트를 동일 적용.
- **수집 채널 (2026-08-13 추가·보강 — wise-FP Stage5 Collector A/B/C + 문서 §수집·정규화 준용)**:
  | 채널 | 방식 | trust_tier 기본 | 비고 |
  |---|---|---|---|
  | 파일 업로드(멀티) | 정형: JSONL/JSON(F6 자동 변환) + **문서: PDF/DOCX/TXT/MD/HTML** — 텍스트 추출 → task 지시 프레임의 **주석 대기(needs_annotation)** 레코드로 수집, 검수 단계에서 정답 작성 | T2_internal | 취약점·대응 보고서 등 (모드 A) |
  | 디렉토리 | **사용자 디렉토리 선택(브라우저 webkitdirectory → 멀티 업로드)** 기본. 서버 경로 glob 은 CLI/ops 용 유지 | T2_internal | 모드 B |
  | 인터넷(URL) | 화이트리스트 + SSRF 차단. **수집 정의**: 응답 유형별 자동 판별 — JSON/JSONL=레코드, HTML/TXT/MD=본문 텍스트 추출 → 주석 대기 레코드 | T3_untrusted | 모드 C, 격리 취급 |
  모든 채널은 동일 정제 게이트(②~⑩) 통과 필수 — 게이트 무우회 원칙. UI 절차 = **①용도 → ②수집 채널 선택 → ③수집 → ④검수 → ⑤증강**.
- 안전성 데이터: 피싱 작성·침해 절차 등 위험 요청은 "범위 제한 + 방어적 대안" 거부 예제로 변환하여
  전체 데이터의 ~10%(가정, 근거 문서 권장 비율) 혼합.

### 7.4 데이터 증강 (F3)

| 기법 | 방식 | 제약 |
|---|---|---|
| 타언어 변환(**역번역**) | **ko→en→ko 왕복 번역**으로 표현 변형(2026-08-13 구체화) — 번역 백엔드는 서빙 스택(Ollama 등) 연동, 미구성 시 비활성 안내 | 기술 용어(CVE/ATT&CK ID/코드)는 불변 보존 |
| 키워드/단어 치환 | 원인/해결방안 내 제품명·프로토콜·자산명 등 동의어·유사 개체 치환. **자동 추천(2026-08-13 추가)**: 승인 레코드에서 빈도 키워드 추출 + 보안 도메인 동의어 사전 매칭 → 치환 후보 제안(확정은 전문가) | 라벨(severity/attack_id) 불변 조건 하에서만; 치환 사전은 도메인 전문가 승인 |
| 패러프레이즈 ✅ | LLM 기반 문장 재구성(`method: paraphrase`, Ollama 백엔드, impl/39th) | 증강본은 `quality_grade=augmented`, 정제 게이트 ⑦ 재통과 |

- 증강본은 원본 `record_id` 계보(lineage) 유지, 원본이 반려되면 증강본도 연쇄 폐기.
- eval/test set은 증강 금지(원본만) — 지표 왜곡 방지.

### 7.5 모델 관리·자동화 (F2·F5)

- **다운로드**: `download_security_llm_models_macos.sh` 로직을 worker 서비스화 — profile(pilot 12/core 28/all 44),
  gated 모델 토큰 처리, 베이스모델 반입 시 GGUF 제외(파인튜닝용 safetensors만), snapshot revision pin +
  manifest(에어갭/N2SF 대비). GGUF/MLX 변환은 학습용 반입과 별도로 **배포 시점**(F11, §7.14)에만 생성한다.
- **튜닝 시작 게이트(2026-08-13 추가)**: 승인(review_state=approved) 레코드가 **최소 500건** 미만인
  데이터셋으로는 튜닝 잡 제출을 차단(경고 배너 + 부족분 안내), 500건 이상부터 제출 가능(가정: 임계값,
  §7.9 `DATASET_MIN_RECORDS`로 옵션화).
- **모델 상태(2026-08-13 추가)**: `registered`(카탈로그 등록만) → `downloading`(로컬 반입 중, 백그라운드)
  → `downloaded`(로컬 스냅샷 존재, 학습 사용 가능) / `pinned`(revision 고정) / `candidate`(이벤트) / `retired`.
  **파이프라인·튜닝은 `downloaded`/`pinned` 모델만 선택 가능**(미다운로드 모델로 학습 불가). 실 다운로드는
  worker(hf CLI, §7.5 download plan) — 코어는 상태 전환(미설치 환경은 시뮬레이션 다운로드로 스냅샷 매니페스트 생성).
- **신규 모델 이벤트**: HF Hub API로 watch 대상(조직/계열/태그) 신규 릴리스 감지 — 감지 방식 옵션
  (기본 polling·주 1회, §7.9) → 유사도 판정(계열·파라미터 규모·라이선스·한국어 지원, 기준 옵션화) →
  후보 등록 → pilot 벤치마크 큐 자동 투입 → 리더보드 비교 후 사람이 채택 결정.
- **야간 배치(F5)**: ops 스케줄러가 트리거 정책 옵션(주기 고정 기본 / 레코드 수 / 토큰 수, §7.9)에 따라 실행 →
  데이터셋 스냅샷 → QLoRA SFT → 평가 게이트(§5 지표 하한 + 이전 버전 대비 회귀 검사) →
  통과 시 어댑터 재배포, 미통과 시 차단·알림·이전 버전 유지. 전 과정 감사로그(append-only).
- **학습 워커(2026-08-13 추가 — wise-FP Stage7 PipelineTrainer 준용)**: 잡 제출 시 **백그라운드 실행**
  (FastAPI BackgroundTasks + asyncio). 승인 데이터셋을 학습 코퍼스로 → QLoRA SFT →
  손실/진행 이벤트 콜백 → 완료 시 어댑터 저장 + **평가 자동 실행 → 리더보드 반영 → 잡 succeeded**.
  torch/transformers/peft/trl 미설치(GPU 없음)면 **시뮬레이션 모드**로 동일 흐름 수행(플랜대로 스텝 진행·
  합성 손실 곡선·홀드아웃 평가) — 파이프라인 전체가 GPU 없이도 end-to-end 동작. 실학습은 의존성 설치 시 자동 전환.
  진행 상황은 잡 이벤트 로그(`GET /tuning/jobs/{id}/events`)로 폴링.

### 7.6 비기능 요구사항 (NFR — 업종 오버레이 반영)

| 항목 | 요구 | 근거 |
|---|---|---|
| 보안 | 학습 데이터·mapping 파일 접근통제(RBAC), 시크릿 관리, 정제 게이트 무우회 원칙 | PIPA·ISMS-P |
| 감사 | 데이터셋 버전·튜닝 잡·배포·롤백 전체 append-only 감사로그 | ISMS-P·전자금융감독규정(finance) |
| 격리 | 모델·데이터 manifest 기반 오프라인 반입 절차 지원(에어갭) | N2SF C/S 등급(govtech) |
| 데이터 | 개인신용정보 반입 금지, 가명정보만 R&D 사용 | 신용정보법(finance) |
| 성능 | 야간 배치 윈도우(가정: 6h) 내 7B급 QLoRA SFT + 평가 완주 | 운영 요구 |
| 가용성 | 재배포 실패 시 자동 롤백, 서빙 무중단 어댑터 교체 | 운영 요구 |
| 관측성 | 튜닝 잡·게이트·배치 OpenTelemetry 메트릭/트레이스, 리더보드 이력 보존 | ict-saas 표준 |

### 7.7 데이터/로깅 요구사항 (지표 측정)

- 평가 리포트(json_valid_rate/attack_f1/severity_accuracy/exact_match)는 모델·데이터셋 버전 쌍으로 영구 보존
- 만족도 이벤트: 질의 ID·모델 버전·score·reason_tags·타임스탬프 (개인 식별자 제외)
- 배치 잡: 트리거 사유·데이터 증분량·소요시간·게이트 결과·배포 여부

### 7.8 외부 연동

- HuggingFace Hub API (모델 검색·다운로드·이벤트), MITRE ATT&CK STIX/TAXII, NVD/CISA KEV 피드,
  Assistant 서비스(질의/답변/만족도 수집 API), 알림 채널(ops 배치 결과)

### 7.9 환경 설정 (운영 옵션 — `.env.example` spec)

§6 확정 옵션 4건은 환경변수로 노출한다. `.env.example` 에 기본값 포함으로 반영하고,
`/wise-dev-standard:env-init` 흐름대로 `.env.{local,dev,staging,prod}` 로 확장한다(환경별 오버라이드 허용).

```bash
# --- Fine-tune batch trigger (F5) ---
FT_TRIGGER_MODE=schedule            # schedule(기본) | record_count | token_count
FT_TRIGGER_SCHEDULE_CRON="0 2 * * *" # schedule 모드: 야간 배치 시각 (가정: 매일 02:00)
FT_TRIGGER_RECORD_THRESHOLD=500      # record_count 모드 임계값
FT_TRIGGER_TOKEN_THRESHOLD=1000000   # token_count 모드 임계값

# --- HF new-model event detection (F2) ---
HF_EVENT_MODE=polling               # polling(기본) | webhook
HF_POLLING_CRON="0 3 * * 1"         # polling 모드: 주 1회 (기본, 월요일 03:00)
HF_WEBHOOK_SECRET=                  # webhook 모드 시 필수
HF_SIMILARITY_CRITERIA=family,param_size,license  # 유사 모델 판정 기준 (조합 옵션)

# --- Satisfaction schema (F4) ---
SATISFACTION_SCALE=binary           # binary(기본, up/down) | likert5(1~5)

# --- Model serving stack ---
SERVING_STACK=ollama                # ollama(기본) | vllm | tgi | llama.cpp | mlx

# --- Dataset minimum for tuning start (2026-08-13 추가) ---
DATASET_MIN_RECORDS=500             # 승인 레코드 이 값 미만이면 튜닝 잡 제출 차단

# --- Resource limits per job (F9, 2026-08-13 추가) ---
JOB_MAX_GPU=1                       # 잡당 GPU 개수 상한 (기본값, 잡 제출 시 개별 오버라이드 가능)
JOB_MAX_VRAM_GB=24                  # 잡당 VRAM 상한(GB)
TOTAL_GPU_CAPACITY=2                # 시스템 전체 동시 학습 GPU 상한 — 초과 시 실제 큐잉(impl/35th 구현,
                                     # JOB_QUEUE_ON_LIMIT=false(즉시 거부)는 미구현, 항상 큐잉)

# --- Deployment export format (F11, 2026-08-13 추가) ---
DEPLOY_EXPORT_DEFAULT=adapter       # adapter(기본, 경량) | full | gguf | mlx
GGUF_QUANT_PRESET=q4_k_m            # Ollama/llama.cpp 변환 시 기본 양자화 프리셋
```

- 저장 스키마는 scale 무관 양쪽 값(`up/down`, `1~5`) 수용(§7.2 satisfaction 필드) — scale 전환 시 기존 데이터 유지.
- 환경별 관례(가정): local/dev = 기본값 유지, staging = prod 동일 설정 리허설, prod = 확정 운영값.
  webhook 은 인바운드 허용 환경(prod)에서만 권장, 망분리(N2SF) 환경은 polling 고정.
- **포트 SSOT 원칙(2026-08-13 추가)**: 프로젝트가 리스닝하는 **모든 포트·바인드 IP는 `.env.*` 가 단일 출처** —
  `API_PORT`/`BIND_HOST`/`POSTGRES_PORT`/`REDIS_PORT` 등. compose·Makefile·프로세스 매니저 설정
  (Procfile/ecosystem.config)은 이 키를 참조만 하고 하드코딩 금지. 포트 충돌 시 `.env.<env>` 수정만으로 해결 가능해야 한다.

## 변경 이력

| 날짜 | 변경 | 근거 |
|---|---|---|
| 2026-08-12 | v0.1 초안. 운영 옵션 4건 확정(§6→§7.9) | 최초 작성 |
| 2026-08-13 | §7.9 포트 SSOT 원칙 추가 — 전체 포트 `.env.*` 관리, 설정 파일 하드코딩 금지 | local-all 포트 충돌 시 env 로 해결 불가했던 결함 |
| 2026-08-13 | E1(데이터셋 코어) 구현 완료 — 게이트 ②④⑤⑥⑦⑨, F6 어댑터(+dpo-pairs/eval-set) | impl/1st·3rd (test/impl/) |
| 2026-08-13 | E2(모델 레지스트리) 구현 완료 — 카탈로그 시드·유사판정·pin/manifest·download plan | impl/4th |
| 2026-08-13 | F7(Supervisor 시험 UI)·F8(파이프라인 CLI) 요구 추가 — §3·§7.10·E8 | Supervisor 용 파이프라인 시험 필요(사용자 요구) |
| 2026-08-13 | E8 구현 완료 — `/supervisor` 경량 UI + `secuftpl` CLI | impl/5th |
| 2026-08-13 | E3~E6 구현 완료 — 튜닝 잡/QLoRA 플랜/평가 러너/리더보드, 키워드 치환 증강, Agent 환류(만족도 stats), 야간 배치(트리거 3모드+평가 게이트). Supervisor ⑤⑥ 활성화(E7-lite) | impl/6th~9th |
| 2026-08-13 | 잔여 명시 — E7 Next.js 본편, GPU worker 실학습, 서빙 어댑터 실교체, 증강 LLM 백엔드, ops cron 배선 | 범위 판단 |
| 2026-08-13 | **E7 정정** — wise-FP frontend "확장" 아님. SecuFTPL 워크스페이스 내 **독립 frontend**(`frontend/`), wise-FP 는 참고만 | 사용자 정정 |
| 2026-08-13 | E7 구현 완료 — `frontend/` Next.js 15(독립): 대시보드·모델·데이터셋·검수큐·튜닝·리더보드 6페이지, rewrites API 프록시, `make front-*` | impl/10th |
| 2026-08-13 | 구동 통합 — `make local-all` 이 web+front 를 프로세스 매니저(pm2/honcho)로 일괄 관리, dev/staging/prod compose 에 `front` 서비스(컨테이너) 추가, FRONT_PORT 전 환경 SSOT | 사용자 요구(구동 방식 통합) |
| 2026-08-13 | §7.11 신설 — Genians 그린 브랜드 스타일(SeCuardian front 준용), 좌측 접이식 사이드바, `/pipeline` 단계별 위저드(자동 다음 이동·이전 복귀·스테퍼 상태 카드) | 사용자 요구(UI 개편 4건) |
| 2026-08-13 | 데이터셋 수집 UX — task_type 선택 시 messages JSONL **자동 템플릿 채움**(근거 문서 §권장 JSONL 포맷·안전 거부 예제의 task별 스키마), 빈 입력 수집 시 422 대신 안내 | 사용자 결함 보고(422) |
| 2026-08-13 | 검수 큐 UX — ①레코드 선택 시 내용(payload) 확인(`GET /records/{id}` 신설) ②**시간 표기 locale 원칙**: API 는 UTC ISO8601, 화면은 `toLocaleString()` 변환 | 사용자 요구 |
| 2026-08-13 | §7.3 수집 채널 확장 — 파일(멀티)·디렉토리·인터넷(URL 화이트리스트) 수집, wise-FP Stage5 Collector A/B/C 준용, trust_tier 태깅 + 게이트 무우회 | 사용자 요구(wise-FP 데이터셋 기능 적용) |
| 2026-08-13 | 데이터셋 고도화 — ①문서 파일(PDF/DOCX/TXT/MD/HTML) 수집→주석 대기 레코드 ②사용자 디렉토리 선택(webkitdirectory) ③URL 수집 정의(응답 유형별 자동 판별) ④UI 절차 재배치(채널 선택→수집→증강) ⑤증강 자동 추천(빈도+도메인 사전)·역번역(ko→en→ko) | 사용자 요구(문서 조사 내용 상세 반영) |
| 2026-08-13 | 검수 큐 삭제 — `DELETE /records/{id}`(증강본 연쇄 삭제 포함), UI 액션 컬럼 '삭제' + 사용자 확인 팝업 | 사용자 요구 |
| 2026-08-13 | 학습 워커(§7.5) — 백그라운드 QLoRA 학습(wise-FP Stage7 준용), torch 미설치 시 시뮬레이션 모드로 end-to-end 동작, 완료 시 자동 평가→리더보드→succeeded, 이벤트 폴링. 리더보드 모델 상세(세부 지표·이력) | 사용자 요구(학습 미진행·리더보드 상세) |
| 2026-08-13 | 잡 후속처리(§7.5) — queued/failed 잡 **재실행**(`POST /jobs/{id}/retry` → 백그라운드 재투입), **삭제**(`DELETE /jobs/{id}`, 이벤트 로그 연쇄 삭제). running 잡은 재실행/삭제 차단 | 사용자 요구(중단 잡 후속처리) |
| 2026-08-13 | 리더보드 후속처리 — ①상세 패널 튜닝 잡 표에도 재실행/삭제 액션 ②**평가 결과 삭제**(`DELETE /leaderboard/{eval_id}`) | 사용자 요구 |
| 2026-08-13 | 튜닝 모니터링·export(§7.5, wise-FP Stage7/9 준용) — ①잡 **진행률**(progress_pct·current_step/total_steps, running 실시간 폴링) ②잡 이벤트 **히스토리** 조회 ③succeeded 잡 **모델 다운로드**(`GET /jobs/{id}/export` — 어댑터 tar.gz 스트리밍) | 사용자 요구(모니터링·모델 export 누락) |
| 2026-08-13 | 모델 상태(F2) — registered→downloading→downloaded 전환(`POST /models/{id}/download`, 백그라운드 시뮬), 파이프라인/튜닝은 downloaded·pinned 만 선택. 파이프라인 **다중 세션**(새 파이프라인 시작·완료 후 리셋). 모델 선택 시 **상세 패널**(다운로드 플랜·스냅샷 매니페스트 등) | 사용자 요구(모델 상태·다중 파이프라인·모델 상세) |
| 2026-08-13 | **고도화 v0.2** — F9(리소스/모니터링 세부설정, Eden-FP·wise-FP ops 참고)·F10(RAG 기반 추가학습·모델 업그레이드)·F11(Ollama/vLLM/llama.cpp/MLX 다중 런타임 배포 + 어댑터 외 풀모델 export)·F12(평가지표 가이드·추천) 신규 스코프, E9~E11 신규 Epic, §7.12~7.14 기술노트, §7.9 env 확장(SERVING_STACK·DATASET_MIN_RECORDS·리소스/export 옵션), 튜닝 시작 최소 데이터셋 500건 게이트 명시 | 사용자 요구(LLM,RAG 문서 반영 고도화) |
| 2026-08-13 | **F9 구현 완료(impl/29th)** — 튜닝 시작 500건 게이트(`DATASET_MIN_RECORDS`), 잡별 `max_gpu`/`max_vram_gb` 리소스 세부설정, `GET /tuning/jobs/{id}/resources`(CPU/메모리 psutil 실측 + GPU pynvml 실측/시뮬레이션). F10~F12 미착수(§8 Epic 잔여 표시) | impl/29th |
| 2026-08-13 | **F10 구현 완료(impl/30th)** — `POST /api/v1/rag/synthesize`·`/upload`(RAG 코퍼스/문서 → 청킹 → cause/resolution 합성 QA → 검수 큐), `POST /api/v1/rag/upgrade`(승인 데이터셋 continual fine-tuning, `continual_from_job_id` 이어학습 참조, 리더보드 공동 등재) | impl/30th |
| 2026-08-13 | **F11 구현 완료(impl/31st)** — `GET /tuning/jobs/{id}/export?format=full`(어댑터 merge 풀모델, real/simulate), `GET .../export-plan?target=gguf\|mlx`(Ollama/llama.cpp/MLX 변환 명령 플랜, 실행 없음) | impl/31st |
| 2026-08-13 | **F12 구현 완료(impl/32nd)** — `GET /api/v1/tuning/eval-guide`(task_type·표본규모 기반 추천 평가지표 세트 + 가이드 문구). **§8 E9~E11 전체 완료** | impl/32nd |
| 2026-08-13 | **frontend F9·F11·F12 연동(impl/33rd)** — tuning 페이지(리소스 입력·모니터링·어댑터/풀모델 다운로드·GGUF/MLX 플랜), leaderboard 페이지(평가지표 가이드 패널). F10 RAG 페이지는 신규 페이지 규모라 다음 이터레이션으로 분리 | impl/33rd |
| 2026-08-13 | **frontend F10 RAG 페이지(impl/34th)** — `/rag` 신규 페이지(코퍼스 합성 텍스트/파일 업로드, 모델 업그레이드 제출), 사이드바 내비게이션 추가. **F9~F12 백엔드+프런트 전체 완료** | impl/34th |
| 2026-08-13 | **F9 실제 리소스 큐잉(impl/35th)** — `TOTAL_GPU_CAPACITY` 기반 `admit_or_queue`/`dispatch_next_queued`(§7.12), 잡 제출·재시도·업그레이드·야간 배치 전 경로 통일. **결함 수정**: 배치(`/batch/run`)가 잡을 생성만 하고 디스패치하지 않아 학습이 전혀 진행되지 않던 문제 해소 | impl/35th |
| 2026-08-13 | **ops cron 배선(impl/36th)** — `GET /api/v1/batch/cron-plan`·`secuftpl batch cron-plan` 로 `FT_TRIGGER_SCHEDULE_CRON`·`HF_POLLING_CRON` crontab 라인 생성(실행/설치 없음), tuning 페이지에 "ops cron 플랜" 버튼 | impl/36th |
| 2026-08-13 | **잡 진행 실시간 스트리밍(impl/37th)** — `WS /tuning/jobs/{id}/stream`(F9 §7.12), tuning 페이지 running 잡별 구독. 구현 중 `websocket.close()` 누락으로 실서버에서 비정상 종료(1006)되는 결함을 실서버+Next.js 프록시 수동 검증으로 발견·수정(pytest TestClient 는 이 결함을 가림) | impl/37th |
| 2026-08-13 | **frontend Vitest/Playwright 배선 + F11 MLX 실 변환(impl/38th)** — 사용자가 잔여 설치 전부 승인, 이 머신(Apple Silicon)에 맞는 항목만 실제 설치·구현·검증(frontend 시험 9건, `mlx-lm`으로 `POST /jobs/{id}/export/mlx` 실행 경로, 공개 초소형 테스트 모델로 실 변환 검증). vLLM·실 QLoRA(bitsandbytes CUDA)·llama.cpp 실행은 하드웨어 미지원 + `_real_available()` 자동전환 위험(발견) 때문에 `.docs/GPU-실학습-배포-가이드.md` 로 별도 문서화 | impl/38th |
| 2026-08-13 | **증강: 패러프레이즈(impl/39th)** — `method: paraphrase`(LLM 문장 재구성, Ollama 백엔드) — §7.4 증강 표 3항목(키워드 치환·역번역·패러프레이즈) 전부 구현 완료. `.docs/GPU-실학습-배포-가이드.md` §1에 §2 형식으로 frontend 시험·MLX 설치 절차 보강(사용자 요청, 문서만) | impl/39th |
| 2026-08-13 | **원스톱 파이프라인 스크립트(impl/40th)** — `scripts/run-pipeline.sh`(F8 확장, §7.10) — 모델 선택→수집→검수→증강→튜닝→게이트→리더보드→배포 전 과정을 curl 오케스트레이션으로 한 번에 실행, 백엔드 자동 기동/정리 포함(사용자 요청) | impl/40th |

### 7.10 Supervisor UI · CLI (F7·F8 — 2026-08-13 추가)

- **Supervisor 시험 UI (F7, 1차)**: FastAPI 가 서빙하는 경량 단일 페이지(`GET /supervisor`) —
  빌드체인·로그인 없음. 흐름: ① 모델 선택(레지스트리 목록/시드) ② 사용용도 선택(task_type)
  ③ 데이터셋 입력/선택(JSONL 붙여넣기 → 검증·수집) ④ 검수 큐 승인/반려 ⑤ 다운로드 플랜 확인.
  파이프라인은 **다중 세션 관리**(2026-08-13 추가): 완료/중단 후 "새 파이프라인" 으로 초기화하고 재구성 가능 —
  진행 상태는 세션별 저장, 완료 시 리셋 유도. (단일 위저드에 갇혀 새 파이프라인을 못 만드는 문제 해소.)
  튜닝 잡 실행 버튼은 E3 완성 시 활성화. **로그인 없음 → BIND_HOST=127.0.0.1 기본, 내부망 전용**
  (외부 노출 시 인증 게이트웨이 필수 — 리스크 §6 연계). 본편 UI 는 **SecuFTPL 독립 frontend**(E7,
  `frontend/` Next.js — wise-FP frontend 는 참고만, 확장·의존 아님. 2026-08-13 정정).
- **CLI (F8)**: `secuftpl` 콘솔 명령(typer) — API 서버 없이 DB 직접 접근으로 동일 파이프라인 실행:
  `dataset validate|convert|ingest|queue|review`, `models seed|list|pin|manifest|scan|download-plan`,
  `batch run|gate|runs|cron-plan`(ops cron 배선 — crontab 라인 생성, 실행/설치 없음, impl/36th).
  야간 배치(ops)·망분리 환경의 스크립팅 진입점.
- **원스톱 파이프라인 스크립트(F8 확장, impl/40th, 2026-08-13 추가)**: `scripts/run-pipeline.sh` —
  HTTP API(FastAPI) 기준으로 전 단계를 curl 로 순차 실행하는 bash 스크립트.
  ① 백엔드 헬스체크(`GET /health`) → 미기동 시 `uv run uvicorn`(= `make dev` 동일 명령) 백그라운드
  기동, 완료 시 트랩(EXIT)으로 자동 종료(스크립트 시작 전부터 이미 떠 있던 서버는 건드리지 않음)
  ② 모델 선택(`models/seed`+`models/{id}/pin`) ③ 데이터셋 수집 — 합성 레코드 N건(기본 500,
  §7.5 게이트와 동일 기준) 일괄 ingest(게이트·가명화·중복제거는 서버측 기존 파이프라인 그대로 적용)
  ④ 검수 승인(queued 전건 approve) ⑤ 증강(옵션, 기본 keyword — Ollama 불필요) ⑥ 튜닝 잡 제출 후
  상태 폴링(succeeded/failed 까지) ⑦ 평가 게이트(§5) ⑧ 리더보드 비교 ⑨ 게이트 통과 시 배포(어댑터
  export, 미통과 시 차단). 각 단계 응답을 `artifacts/pipeline-run-<timestamp>/` 에 JSON/아티팩트로
  저장. 신규 백엔드 코드 변경 없음 — 기존 API 만 오케스트레이션(`make`/`curl`/`jq` 의존).

### 7.11 Frontend 디자인·내비게이션 (E7 보강 — 2026-08-13 추가)

- **브랜드 스타일**: SeCuardian·SeCuardian-Marketplace front 준용 — Genians CI 그린(#86BC25)
  팔레트(주 액션 #6fa01c, 강조 #567d15, 배경 틴트 #f6fae9), 시스템 폰트 스택 유지.
- **내비게이션**: 상단 메뉴 → **좌측 접이식 사이드바**(펼침/접힘 토글, 대시보드~리더보드 + 파이프라인).
- **파이프라인 위저드**(`/pipeline`): 모델 선택 → 데이터셋 수집(게이트·가명화·중복제거) → 검수 승인 →
  (증강, 건너뛰기 가능) → 튜닝 잡 → 평가 게이트 → 리더보드 비교 → 배포 — **단계 완료 시 자동 다음 이동**,
  **이전 단계 복귀 허용**. 단계별 상태(완료/진행/대기/건너뜀)를 스테퍼 카드로 시각화
  (참고: LLM Development Stages 단계 카드 레이아웃). 개별 페이지는 사이드바로 직접 접근 유지.

### 7.12 리소스/모니터링 세부설정 (F9 — Eden-FP·wise-FP ops 참고, 2026-08-13 추가)

- **리소스 세부설정**: 잡 제출 시 GPU 개수/VRAM 상한/CPU·워커 슬롯/배치 크기를 지정(미지정 시 프로파일 기본값).
  ops 스케줄러가 상한을 초과하는 동시 잡은 큐잉(F5 야간 배치와 동일 큐 공유).
- **실시간 모니터링 대시보드**: 잡별 GPU util·VRAM 사용량·throughput(tokens/s)·ETA·손실 곡선을
  폴링(`GET /tuning/jobs/{id}/resources`)으로 노출. wise-FP ops 리소스 매니저 화면 구성 준용.
- **WebSocket 진행 스트리밍(impl/37th 구현)**: `WS /tuning/jobs/{id}/stream` — 0.3초 주기로
  상태·진행률·신규 이벤트 push, succeeded/failed 도달 시 최종 스냅샷 후 정상 종료. 폴링(`/events`)
  대안(둘 다 유지). frontend tuning 페이지는 running 잡마다 자동 구독.
- **백그라운드 지속성**: 튜닝 잡은 §7.5 학습 워커와 동일하게 서버 프로세스에 귀속 — 사용자가 다른 메뉴로
  이동해도 잡은 계속 진행되며, 재진입 시 이벤트 로그·리소스 그래프를 이어서 조회(히스토리 보존).
- **가드레일**: 리소스 상한 미설정 시 시스템 기본 프로파일 적용, GPU 미탑재 환경은 시뮬레이션 모드로
  리소스 지표도 합성값 표기(라벨 `simulated`).
- **실제 큐잉(impl/35th 구현)**: `TOTAL_GPU_CAPACITY` 기준 현재 `running` 잡의 `max_gpu` 합 +
  신규 잡 `max_gpu` 가 상한을 넘으면 `queued` 유지(즉시 시작하지 않음). 잡 완료(성공/실패) 시
  가장 오래 대기한 `queued` 잡을 FIFO로 재확인해 상한 내면 시작(`dispatch_next_queued`) —
  선두 잡이 상한을 초과하면 뒤쪽의 더 작은 잡을 건너뛰어 먼저 시작하지 않는다(head-of-line
  blocking, 의도적 단순화). 잡 제출(F1)·재실행(재시도)·업그레이드(F10)·야간 배치(F5) 모두
  동일 디스패처(`admit_or_queue`)를 공유 — 배치가 잡을 생성만 하고 디스패치하지 않던 결함도
  이때 함께 해소.

### 7.13 RAG 기반 추가학습·모델 업그레이드 (F10, 2026-08-13 추가)

```text
[RAG 코퍼스]                    [합성]                  [학습]                 [평가/승격]
문서/URL(F3 채널 재사용) →  청킹→임베딩(참고용,        기존 데이터셋 +      §5 평가 게이트 +
벡터DB(운영 중인 RAG 시스템   Out of Scope 시스템 연동  합성 QA로            이전 버전 대비 회귀검사
 또는 업로드 문서)             or 로컬 청킹) →           continual FT       → 통과 시 model_version++
                              QA/지식 페어 합성           (base+기존 어댑터   (업그레이드), 미통과 시
                              (LLM 기반, cause/resolution  이어서 학습)       기존 버전 유지
                              스키마 §7.2 재사용) →
                              §7.3 정제 게이트 통과 필수
```

- 합성 데이터도 canonical 스키마(§7.2) 준수, `source_type=rag_synthesis`로 태깅해 원본 문서까지 계보 추적.
- 업그레이드 대상은 `downloaded`/`pinned` 베이스모델 + 기존 배포 어댑터(선택) 조합. 신규 베이스 학습이 아닌
  **이어학습(continual)** 이 기본이며, 처음부터 재학습(from-scratch)은 옵션.
- 결과 모델은 리더보드에 기존 모델과 나란히 등재해 비교 후 승격 여부 결정(F1 재사용).

### 7.14 다중 런타임 배포·풀모델 export (F11, 2026-08-13 추가)

| 런타임 | 배포 아티팩트 | 변환 |
|---|---|---|
| Ollama | GGUF(+ Modelfile) | 어댑터 merge → safetensors → GGUF 양자화(가정: q4_k_m 기본) |
| vLLM | 풀모델 safetensors (merge된 가중치) | 어댑터 merge, 양자화 불필요(옵션: AWQ/GPTQ) |
| llama.cpp | GGUF | Ollama와 동일 변환 경로 공유 |
| MLX(Apple Silicon) | MLX 포맷(mlx_lm 변환) | safetensors → MLX 변환, macOS 로컬 서빙 대상 |

- 배포 단계에서 **어댑터만(경량)** 또는 **풀모델(merge)** 다운로드를 선택 가능 — 풀모델은 런타임별 위 표
  아티팩트로 export(`GET /jobs/{id}/export?format=adapter|full|gguf|mlx`).
- 변환은 배포 시점에만 수행(§7.5 다운로드 게이트와 무관), 변환 후 스모크 평가(§6 리스크) 자동 실행.
- 라이선스 제약(HF gated 모델 파생물 재배포 조건)은 §6 리스크와 동일 적용 — 런타임 무관 공통 검토.
- **MLX 실 변환(impl/38th 구현)**: `mlx-lm`(Apple Silicon, `uv sync --extra mlx`) 로
  `POST /jobs/{id}/export/mlx` 가 명령 플랜을 넘어 **실제 변환을 실행**. 풀모델이 실 HF 가중치가
  아니면(현재 `merge_full_model` 은 peft/torch 미설치라 시뮬레이션 매니페스트만 생성) 422로
  실패 원인을 그대로 노출(가짜 성공 없음). GGUF(llama.cpp)는 리포지토리 클론·빌드가 필요해
  여전히 명령 플랜만 유지(`.docs/GPU-실학습-배포-가이드.md` §2.3).
  실 QLoRA 학습(§7.5)은 CUDA 전용(bitsandbytes) + `_real_available()` 설치 시 테스트 스위트
  자동전환 위험이 있어 별도 GPU 환경 가이드로 분리(같은 문서 §2.2).

## 8. 실행 연결 (Epic / Story 힌트)

| Epic | 내용 | 의존 |
|---|---|---|
| E1. 데이터셋 코어 | canonical 스키마·포맷 어댑터(F6)·정제 게이트·검수 큐 | — |
| E2. 모델 레지스트리 | HF 다운로드 서비스화·revision pin·manifest·신규 모델 이벤트(F2) | — |
| E3. 튜닝·평가 | QLoRA SFT worker 확장·다중 모델 병렬·평가 러너·리더보드(F1) | E1, E2 |
| E4. 증강 | 타언어 변환·키워드 치환·lineage 관리(F3) | E1 |
| E5. Agent 환류 | 질의/답변/만족도 수집 API·환류 정제 규칙(F4) | E1 |
| E6. 자동화 | 야간 배치 스케줄러·평가 게이트·재배포/롤백(F5) | E3, E5 |
| E7. Frontend | **SecuFTPL 독립 frontend**(`frontend/` Next.js 앱) — 대시보드·모델·검수 큐·리더보드·튜닝. wise-FP frontend 는 **참고만**(로그인 등 제외), 확장 아님 | E1~E6 병행 |
| E8. Supervisor UI·CLI | 경량 내장 시험 UI(F7 1차) + `secuftpl` CLI(F8) | E1, E2 |
| E9. 리소스/모니터링 ✅ | 잡별 리소스 세부설정·실시간 모니터링 대시보드·백그라운드 지속성(F9) — impl/29th | E3 |
| E10. RAG 추가학습 ✅ | RAG 코퍼스 합성 데이터 파이프라인·continual FT·모델 버전 승격(F10) — impl/30th | E1~E3 |
| E11. 다중 런타임 export ✅ | 어댑터 merge·GGUF/MLX 변환 플랜·런타임별 배포 아티팩트·평가지표 가이드(F11·F12) — impl/31st~32nd | E3 |

권장 순서: E1·E2 병행 → E3 → E4·E5 병행 → E6 → (E7·E9는 각 Epic과 병행) → E10 → E11.
근거 문서 90일 로드맵과 정합.
