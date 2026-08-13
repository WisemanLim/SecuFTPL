# COMPLIANCE — 정보통신·SaaS (ICT / SaaS) (KSIC J)

> 자동 생성 (wise-dev-standard / scaffold). 근거: `domains/ict-saas.yaml` + KSIC 통합표.
> 규제는 변하므로 하단 References 로 재확인할 것.
> PRD §6 오버레이: 고객 업종에 따라 **govtech(N2SF)·finance(신용정보법)** 델타를 추가 적용한다.

## 분류 / Classification

| 체계 | 값 |
|---|---|
| KSIC | J (58, 59, 60, 61, 62, 63) |
| ISIC / NACE | J |
| NAICS | 51 |

## 한국 규제 (1순위)

| 규제 | 시행/기준 | 영향 |
|---|---|---|
| 정보통신망법 | — | 네트워크·정보보호 의무(§47=ISMS 근거), 침해사고 신고 |
| 개인정보보호법(PIPA) | — | PII 동의·최소화·유출통지(§32-2) — 학습 데이터 비식별화 게이트와 직결 |
| ISMS-P | 3년 주기 | 대형 ICT 서비스 의무, 접근로그·변경관리·암호화 증적 |
| CSAP(클라우드) | 2025 온라인 발급 | 공공/정부 클라우드 판매 시 IaaS/SaaS/DaaS 인증 |

### PRD 오버레이 델타 (고객 업종별 추가)

| 도메인 | 규제 | 플랫폼 영향 |
|---|---|---|
| govtech | N2SF(C/S/O 등급) 망분리, CSAP | 모델·데이터 manifest + revision pin 필수(에어갭 반입), `HF_EVENT_MODE=polling` 고정 |
| finance | 신용정보법, 전자금융감독규정(2025-02-05) | 개인신용정보 학습 데이터 반입 금지 — 가명정보만 R&D 사용, append-only 감사로그 |

## 국제 기준

- SOC 2 Type II (US SaaS, 6~12개월 통제)
- ISO/IEC 27001 (SOC2와 40~85% 통제 중첩)
- GDPR (EU 고객/테넌트)

## 데이터 등급

| 데이터 | 등급 | 비고 |
|---|---|---|
| 테넌트 데이터 | 민감 | 고객별 격리(RLS/스키마/DB) |
| 고객 PII | 민감 | PIPA/GDPR — **비-프로덕션(dev/staging/test)에 실데이터 반입 금지** |
| 인증/아이덴티티(RBAC) | 규제대상 | 접근통제 — **비-프로덕션 실데이터 반입 금지** |
| 감사로그/텔레메트리 | 내부 | SOC2/ISO 보관·삭제정책 |
| (PRD 추가) 학습 데이터셋 | 민감 | 정제 게이트(비식별화·가명화) 통과분만 반입, mapping 파일 접근통제 |
| (PRD 추가) 개인신용정보 | 규제대상 | finance 고객 시 반입 자체 금지(가명정보만) |

## 인프라 패턴

- 멀티테넌트 격리(RLS/스키마/DB-per-tenant)
- 관측성(OTel 콜렉터→티어드 스토리지, 검증된 삭제 CC6.5/A.8.10)
- 피처플래그, API 게이트웨이, 수평 오토스케일, 시크릿 관리
- 표준 CI/CD
- stack_overrides: PostgreSQL + Redis(캐시/큐), OpenAPI 계약(API-first)

## 개발환경 특수 요구

- 테넌트 격리 테스트(크로스테넌트 누출 단언, RLS 강제)
- 텔레메트리 보관/삭제 검증(CC6.5/A.8.10), OpenAPI 계약 테스트
- SOC2/ISO 통제 증적 자동화(접근로그·변경관리)
- (PRD 추가) 학습 데이터 정제 게이트 무우회 원칙 — 게이트 미통과 데이터의 학습 투입 차단 테스트

## 추가 시험 (test/ 반영)

- 크로스테넌트 데이터 누출 차단(RLS)
- OpenAPI 계약 적합성(contract test)
- 감사로그 보관기간 경과 삭제 증명
- (PRD 추가) 비밀값/PII 스캐너 회귀 테스트(SECRET_PATTERNS), split 시간·사건 분리 검증

## 출처 / References

- https://isms-p.or.kr/sysm/intro/selectSysmCertDetail.do (ISMS-P)
- https://isms.kisa.or.kr/main/csap/notice/ (CSAP 2025)
- https://secureframe.com/blog/soc-2-vs-iso-27001
- https://oneuptime.com/blog/post/2026-02-06-telemetry-retention-soc2-iso27001/view
- https://www.fsc.go.kr/no010101/82885 (전자금융감독규정 — finance 델타)
- https://zdnet.co.kr/view/?no=20250124164856 (N2SF — govtech 델타)
