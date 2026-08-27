# SecuFTPL-Survey — Fine-Tuning 참고 소스 조사

> 작성: 2026-08-27 · 근거: `pub-star-classifier` 스타 분석(`WisemanLim-stars-20260827-165635.md`, 총 5,683 레포) + 기술·시장 동향 웹 조사
> 목적: SecuFTPL(보안 도메인 LLM Fine-Tune 파이프라인)의 데이터셋 구축·학습·평가·배포 각 단계에서 참고할 오픈소스·논문·동향을 한곳에 정리 (PRD §7 각 절과 매핑)

## 1. 스타 레포 분석 — Fine-Tuning 직접 참고 소스

스타 5,683개 중 FT 파이프라인 관련 키워드(fine-tune/LoRA/QLoRA/SFT/DPO/dataset/quantize/eval 등)로
추출·선별. SecuFTPL 단계별 매핑.

### 1.1 학습 프레임워크 (PRD E3 — QLoRA SFT worker, §7.5)

| 프로젝트 | 설명 | Stars | License | SecuFTPL 참고 포인트 |
|---|---|---:|---|---|
| [unslothai/unsloth](https://github.com/unslothai/unsloth) | 로컬 LLM 학습/실행 UI·커널 최적화 (Qwen/Gemma/DeepSeek 등) | 74,922 | Apache-2.0 | 단일 GPU QLoRA 최적화 — 야간 배치 윈도우(6h) 내 완주에 핵심. 실학습 전환 시 1순위 후보 |
| [hiyouga/LlamaFactory](https://github.com/hiyouga/LlamaFactory) | 100+ LLM/VLM 통합 효율 파인튜닝 (ACL 2024) | 74,390 | Apache-2.0 | YAML 설정 기반 다중 모델 학습 — F1(다중 베이스모델 병렬 비교) 구현 패턴, 웹 UI 참고 |
| [deepspeedai/DeepSpeed](https://github.com/deepspeedai/DeepSpeed) | 분산 학습·추론 최적화(ZeRO) | 43,002 | Apache-2.0 | 다중 GPU 확장 시(F9 리소스 상한) 백엔드 |
| [Lightning-AI/pytorch-lightning](https://github.com/Lightning-AI/pytorch-lightning) | 규모 무관 학습 프레임워크 | 31,310 | Apache-2.0 | trainer 추상화 — 시뮬레이션↔실학습 전환 구조 참고 |
| [karpathy/llm.c](https://github.com/karpathy/llm.c) | C/CUDA 단순 LLM 학습 | 30,882 | MIT | 학습 루프 원리 학습용 |
| [huggingface/trl](https://github.com/huggingface/trl) | RL 기반 트랜스포머 학습(SFT/DPO/GRPO) | 19,158 | Apache-2.0 | 현 SecuFTPL 학습 워커 의존성 — DPO 확장(Out of Scope→2차) 시 그대로 사용 |
| [tloen/alpaca-lora](https://github.com/tloen/alpaca-lora) | 소비자 HW instruct-tune 원조 | 18,906 | Apache-2.0 | 최소 LoRA SFT 레퍼런스 |
| [meta-llama/llama-cookbook](https://github.com/meta-llama/llama-cookbook) | Llama 공식 FT/RAG 가이드 | 18,558 | MIT | gated 모델(Llama) FT·라이선스 조건(PRD §6 리스크) 공식 근거 |
| [oumi-ai/oumi](https://github.com/oumi-ai/oumi) | 오픈 LLM FT·평가·배포 원스톱 | 9,374 | Apache-2.0 | FT→eval→deploy 전주기 플랫폼 — SecuFTPL 과 동일 지향, 구조 비교 대상 |
| [EleutherAI/gpt-neox](https://github.com/EleutherAI/gpt-neox) | Megatron+DeepSpeed 병렬 학습 | 7,459 | Apache-2.0 | 대규모 사전학습(Out of Scope) 경계 참고 |
| [InternLM/xtuner](https://github.com/InternLM/xtuner) | 초대형 MoE 학습 엔진 | 5,183 | Apache-2.0 | MoE 계열 베이스모델 채택 시 |
| [h2oai/h2o-llmstudio](https://github.com/h2oai/h2o-llmstudio) | 노코드 FT GUI | 5,172 | Apache-2.0 | Supervisor UI(F7)·frontend(E7) 화면 흐름 벤치마크 |
| [MakazhanAlpamys/Soup](https://github.com/MakazhanAlpamys/Soup) | YAML 하나로 FT, 4GB GPU 에서 8B 학습(layer streaming) | 3,205 | Apache-2.0 | 저사양 GPU 학습 기법 — 온프레미스 고객 환경 대응 |
| [Blaizzy/mlx-vlm](https://github.com/Blaizzy/mlx-vlm) | Mac(MLX) VLM 추론·FT | 5,423 | MIT | 멀티모달 2차 릴리즈(PRD Out of Scope) 대비 |
| [kongds/MoRA](https://github.com/kongds/MoRA) | High-Rank PEFT 기법 | 361 | Apache-2.0 | LoRA 변형 기법 연구 |
| [Memento-Teams/Memento](https://github.com/Memento-Teams/Memento) | LLM 을 FT 하지 않는 에이전트 적응 | 2,569 | MIT | FT 대안(메모리 기반) — RAG vs FT 경계 논의(PRD §7.1 분리 원칙) |
| [hyunwoongko/nanoRLHF](https://github.com/hyunwoongko/nanoRLHF) | RLHF from-scratch | 197 | Apache-2.0 | 선호학습 내부 원리 |
| [0xSojalSec/notebooks-fine-tuning](https://github.com/0xSojalSec/notebooks-fine-tuning) | FT·RL 노트북 250+ | 62 | LGPL-3.0 | 기법별 실습 카탈로그 |
| [daekeun-ml/sagemaker-finetune-serve-e2e](https://github.com/daekeun-ml/sagemaker-finetune-serve-e2e) | Gemma FT E2E(합성데이터→LoRA/QLoRA→GRPO→서빙→평가) | 8 | MIT | 클라우드 E2E 트랙 구성 — 파이프라인 단계 설계 대조 |
| [gyunggyung/KoGPT2-FineTuning](https://github.com/gyunggyung/KoGPT2-FineTuning) | 한국어 GPT-2 FT 사례 | 228 | Apache-2.0 | 한국어 도메인 FT 선례 |

### 1.2 데이터셋 구축·합성·정제 (PRD E1·F3·F13~F15 — §7.3 수집·정제 파이프라인)

| 프로젝트 | 설명 | Stars | License | SecuFTPL 참고 포인트 |
|---|---|---:|---|---|
| [huggingface/datasets](https://github.com/huggingface/datasets) | 데이터셋 허브·처리 표준 | 21,872 | Apache-2.0 | F6 포맷 어댑터의 HF datasets 호환 export 확장 후보 |
| [allenai/olmocr](https://github.com/allenai/olmocr) | LLM 학습용 PDF 선형화 툴킷 | 19,396 | Apache-2.0 | F3 문서 수집 채널(PDF→주석대기 레코드) 품질 개선 — 현 pypdf 대비 상위 대안 |
| [ConardLi/easy-dataset](https://github.com/ConardLi/easy-dataset) | FT/RAG/Eval 용 데이터셋 생성 도구 | 14,836 | 비표준 | 문서→QA 데이터셋 UI 흐름 — F10 RAG 합성·검수 큐와 직접 비교 대상 |
| [mlabonne/llm-datasets](https://github.com/mlabonne/llm-datasets) | post-training 데이터셋·도구 큐레이션 | 4,758 | - | 공개 데이터셋 수입(P1 소스) 선정 기준 |
| [verazuo/jailbreak_llms](https://github.com/verazuo/jailbreak_llms) | 15,140 프롬프트(1,405 jailbreak) 데이터셋 (CCS'24) | 3,793 | MIT | **안전 거부 예제(safety_refusal task) 원천 데이터** — PRD §7.3 안전성 ~10% 혼합에 직접 활용 가능 |
| [Zjh-819/LLMDataHub](https://github.com/Zjh-819/LLMDataHub) | instruction FT 데이터셋 가이드 | 3,411 | MIT | 포맷/품질 기준 비교 |
| [wasiahmad/Awesome-LLM-Synthetic-Data](https://github.com/wasiahmad/Awesome-LLM-Synthetic-Data) | LLM 합성 데이터 리딩리스트 | 1,551 | MIT | F10 합성 QA·§7.4 증강 기법 문헌 지도 |
| [InternScience/GraphGen](https://github.com/InternScience/GraphGen) | 지식 그래프 기반 SFT 합성 데이터 생성 | 1,212 | Apache-2.0 | RAG 코퍼스→합성 QA(F10) 품질 고도화 — 지식 커버리지 기반 생성 |
| [gretelai/gretel-synthetics](https://github.com/gretelai/gretel-synthetics) | 차등정보보호 합성 데이터 | 683 | 비표준 | PII 민감 데이터(§7.3 게이트 ④⑤) 의 DP 합성 대안 |
| [sdv-dev/SDV](https://github.com/sdv-dev/SDV) | 정형 합성 데이터 | 3,549 | 비표준 | 로그/이벤트(정형) 합성 |
| [kaistAI/CoT-Collection](https://github.com/kaistAI/CoT-Collection) | CoT FT 데이터셋 (EMNLP 2023) | 258 | - | 원인 분석(cause) 필드의 추론 체인 데이터 설계 |
| [lcw99/evolve-instruct](https://github.com/lcw99/evolve-instruct) | Evol-Instruct 다국어 변형 | 120 | - | §7.4 증강(패러프레이즈/난이도 진화) 기법 |
| [dsdanielpark/open-llm-datasets](https://github.com/dsdanielpark/open-llm-datasets) | 오픈 LLM 데이터셋·논문 정리 | 100 | MIT | 출처·라이선스 정리 사례(F14 attribution 관점) |
| [HumanSignal/label-studio](https://github.com/HumanSignal/label-studio) | 멀티타입 라벨링 플랫폼 | 28,153 | Apache-2.0 | 검수 큐(⑨ 사람 검수) 고도화 — 라벨링 워크플로·다중 검수자 참고 |
| [haykgrigo3/TimeCapsuleLLM](https://github.com/haykgrigo3/TimeCapsuleLLM) | 특정 시기 데이터만 학습(편향 통제) | 1,975 | MIT | 시간 단위 split(§7.3 ⑧ 랜덤 split 금지) 근거 사례 |

### 1.3 문서 수집·파싱 (PRD F3 수집 채널 — PDF/DOCX/HTML/URL)

| 프로젝트 | 설명 | Stars | License | SecuFTPL 참고 포인트 |
|---|---|---:|---|---|
| [microsoft/markitdown](https://github.com/microsoft/markitdown) | 오피스 문서→Markdown | 176,541 | MIT | 문서 수집 채널 확장(PPT/XLSX 등) 1순위 |
| [opendatalab/MinerU](https://github.com/opendatalab/MinerU) | PDF/오피스→LLM-ready MD/JSON | 78,585 | 비표준 | 복잡 레이아웃 보안 보고서 파싱 |
| [docling-project/docling](https://github.com/docling-project/docling) | GenAI 용 문서 전처리(IBM) | 65,620 | MIT | 표·구조 보존 파싱 — CTI 보고서의 IOC 표 추출 |
| [unclecode/crawl4ai](https://github.com/unclecode/crawl4ai) | LLM 친화 웹 크롤러 | 79,488 | Apache-2.0 | URL 수집 채널(모드 C) 고도화 — 단 SSRF/화이트리스트 정책은 SecuFTPL 게이트 유지 |
| [firecrawl/firecrawl](https://github.com/firecrawl/firecrawl) | 웹 검색·스크랩 API | 172,957 | AGPL-3.0 | 상용급 수집 API 참고(AGPL 주의 — 상용화 시 §6 라이선스 검토) |
| [datalab-to/marker](https://github.com/datalab-to/marker) | PDF→MD+JSON 고정밀 변환 | 39,303 | Apache-2.0 | PDF 파싱 대안 |
| [datalab-to/surya](https://github.com/datalab-to/surya) | 90+ 언어 OCR·레이아웃 | 21,318 | Apache-2.0 | 스캔 문서(이미지 PDF) 대응 |
| [pymupdf/PyMuPDF](https://github.com/pymupdf/PyMuPDF) | 고성능 PDF 처리 | 10,581 | AGPL-3.0 | 현 pypdf 대비 성능 대안(AGPL 주의) |

### 1.4 평가·검증 (PRD F1 리더보드·F12 평가지표 가이드 — §5)

| 프로젝트 | 설명 | Stars | License | SecuFTPL 참고 포인트 |
|---|---|---:|---|---|
| [EleutherAI/lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness) | 표준 few-shot 평가 하네스 | 13,808 | MIT | 평가 러너 표준 태스크 연동 — 커스텀 보안 태스크(YAML) 등록 방식 참고 |
| [confident-ai/deepeval](https://github.com/confident-ai/deepeval) | LLM 평가 프레임워크(단위테스트 스타일) | 17,892 | Apache-2.0 | G-Eval·환각 지표 — 만족도 외 자동 평가 보강 |
| [Arize-ai/phoenix](https://github.com/Arize-ai/phoenix) | AI 관측·평가 | 11,210 | 비표준 | 운영 중 응답 품질 추적(F4 환류와 결합) |
| [Giskard-AI/giskard-oss](https://github.com/Giskard-AI/giskard-oss) | LLM 에이전트 평가·테스트 | 5,773 | Apache-2.0 | 취약점(주입·유해성) 스캔 — 배포 전 게이트 보강 |
| [langwatch/langwatch](https://github.com/langwatch/langwatch) | LLM 평가·에이전트 테스트 플랫폼 | 3,514 | Apache-2.0 | 리더보드 UX 참고 |
| [lm-sys/FastChat](https://github.com/lm-sys/FastChat) | 학습·서빙·평가(Arena) | 39,525 | Apache-2.0 | 모델 간 pairwise 비교(Arena 방식) — 리더보드 확장 아이디어 |
| [HAE-RAE/haerae-evaluation-toolkit](https://github.com/HAE-RAE/haerae-evaluation-toolkit) | 한국어 LLM 평가 툴킷 | 70 | Apache-2.0 | **한국어 보안 용어 평가** — 한국어 성능 비교(F1) 보강 |
| [daekeun-ml/evaluate-llm-on-korean-dataset](https://github.com/daekeun-ml/evaluate-llm-on-korean-dataset) | 한국어 벤치마크 경량 실행 | 48 | MIT | 한국어 기준선 측정 |
| [Andyyyy64/whichllm](https://github.com/Andyyyy64/whichllm) | 하드웨어별 로컬 LLM 추천 벤치마크 | 6,491 | MIT | 베이스모델 선정(F2 유사판정) 보조 지표 |

### 1.5 배포·서빙·양자화 (PRD F11 다중 런타임 — §7.14)

| 프로젝트 | 설명 | Stars | License | SecuFTPL 참고 포인트 |
|---|---|---:|---|---|
| [ollama/ollama](https://github.com/ollama/ollama) | 로컬 모델 실행 표준 | 179,533 | MIT | 현 기본 서빙 스택(§7.9 SERVING_STACK) |
| [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp) | C/C++ LLM 추론(GGUF) | 125,851 | MIT | GGUF 변환 경로(§7.14) 원천 |
| [vllm-project/vllm](https://github.com/vllm-project/vllm) | 고처리량 서빙 엔진 | 90,189 | Apache-2.0 | GPU 서버 배포 대상 |
| [vllm-project/llm-compressor](https://github.com/vllm-project/llm-compressor) | vLLM 용 압축(AWQ/GPTQ 등) | 3,729 | Apache-2.0 | §7.14 vLLM 양자화 옵션 구현체 |
| [vllm-project/production-stack](https://github.com/vllm-project/production-stack) | K8s 클러스터 배포 레퍼런스 | 2,528 | Apache-2.0 | 운영 배포 아키텍처 |
| [ml-explore/mlx](https://github.com/ml-explore/mlx) · [mlx-lm](https://github.com/ml-explore/mlx-lm) · [mlx-examples](https://github.com/ml-explore/mlx-examples) | Apple Silicon 프레임워크·LLM 실행·예제 | 28,180 / 6,805 / 8,908 | MIT | MLX export(F11, impl/38th 실변환) 의존성. mlx-lm 은 LoRA FT 도 지원 — Mac 로컬 실학습 후보 |
| [turboderp-org/exllamav3](https://github.com/turboderp-org/exllamav3) | 소비자 GPU 양자화·추론 | 1,170 | MIT | 저사양 배포 포맷 추가 후보 |
| [huawei-csl/SINQ](https://github.com/huawei-csl/SINQ) | 신규 고품질 양자화(ICML 2026) | 629 | Apache-2.0 | 변환 후 정밀도 손실(§6 리스크) 완화 기법 |
| [cactus-compute/cactus](https://github.com/cactus-compute/cactus) | 모바일/엣지 양자화·런타임 | 5,935 | 비표준 | 엣지 배포 확장 시 |

### 1.6 안전·가드레일·보안 도메인 (PRD §6 리스크·안전 거부 데이터)

| 프로젝트 | 설명 | Stars | License | SecuFTPL 참고 포인트 |
|---|---|---:|---|---|
| [NVIDIA-NeMo/Guardrails](https://github.com/NVIDIA-NeMo/Guardrails) | 프로그래머블 가드레일 | 7,019 | 비표준 | 배포 모델 앞단 거부/주입 방어 — 게이트 ②(주입 탐지)와 상보 |
| [EasyJailbreak/EasyJailbreak](https://github.com/EasyJailbreak/EasyJailbreak) | 탈옥 프롬프트 생성 프레임워크 | 891 | GPL-3.0 | 배포 전 레드팀 평가(방어 목적) — 안전 거부 학습 검증 |
| [verazuo/jailbreak_llms](https://github.com/verazuo/jailbreak_llms) | (재게재) 탈옥 프롬프트 데이터셋 | 3,793 | MIT | 안전 거부 예제 소스 |
| [A-poc/BlueTeam-Tools](https://github.com/A-poc/BlueTeam-Tools) | 블루팀/IR 기법 모음 | 4,456 | - | 원인/해결방안(resolution) 정답 작성 시 절차 지식 소스(P1) |
| [adobe/OSAS](https://github.com/adobe/OSAS) | 로그 이상탐지(사전라벨링+ML) | 156 | Apache-2.0 | SOC 경보 데이터 사전 라벨링 파이프라인 참고 |

> 참고(에이전트형, FT 아님): [0x4m4/hexstrike-ai](https://github.com/0x4m4/hexstrike-ai) (보안 도구 MCP 오케스트레이션, 11,387★),
> [0xSteph/pentest-ai-agents](https://github.com/0xSteph/pentest-ai-agents) (공격 리서치 에이전트, 2,166★) —
> SecuFTPL 은 방어 목적 한정(PRD Out of Scope)이므로 데이터 소스가 아닌 **활용처(Assistant 통합)** 관점만 참고.

## 2. 기술·시장 동향 (웹 조사, 2026-08 기준 — 링크는 검색 확인분만)

### 2.1 LLM Fine-Tuning 기법 동향

#### PEFT / LoRA 계열

| 주제 | 핵심 내용 | 링크 |
|---|---|---|
| QLoRA | 4-bit NF4 양자화 + LoRA로 단일 GPU에서 65B급 파인튜닝 — 여전히 사실상 표준 (Dettmers et al.) | [arXiv:2305.14314](https://arxiv.org/abs/2305.14314) |
| DoRA (ICML 2024 Oral) | 가중치를 크기·방향으로 분해, 방향에만 LoRA → LoRA 대비 LLaMA-7B +3.7%. HF PEFT `use_dora=True` 지원 | [arXiv:2402.09353](https://arxiv.org/abs/2402.09353) · [NVlabs/DoRA](https://github.com/NVlabs/DoRA) |
| rsLoRA | 스케일링 α/r → α/√r 수정으로 고랭크 그래디언트 붕괴 방지 | [arXiv:2312.03732](https://arxiv.org/abs/2312.03732) |
| LoRA 변형 통합 연구 | 변형 분류·실증 평가(2026). 랭크 32~64가 용량/안정성 최적이라는 실증 다수 | [arXiv:2601.22708](https://arxiv.org/pdf/2601.22708) · [LoRA 서베이(FCS 2024)](https://dl.acm.org/doi/10.1007/s11704-024-40663-9) |
| 도메인 LoRA 벤치마크 | FinLoRA: 금융 데이터셋에서 LoRA/QLoRA/rsLoRA/DoRA 비교 — **"보안 도메인 LoRA 벤치" 설계에 직접 참고** | [arXiv:2505.19819](https://arxiv.org/html/2505.19819v1) |

#### 선호학습 (Preference Optimization)

| 기법 | 핵심 내용 | 링크 |
|---|---|---|
| DPO | 보상모델·PPO 없이 선호쌍 분류 손실만으로 정렬 | [arXiv:2305.18290](https://arxiv.org/abs/2305.18290) |
| KTO | 선호 쌍 불필요 — 단건 👍/👎 이진 라벨 학습 — **SecuFTPL 만족도(binary) 환류와 정확히 일치** | arXiv:2402.01306 · [awesome-DPO 정리](https://github.com/liushunyu/awesome-direct-preference-optimization) |
| ORPO | 참조모델 없이 SFT+정렬 단일 스테이지(odds-ratio) — 파이프라인 단순화 | [arXiv:2403.07691](https://arxiv.org/abs/2403.07691) |
| GRPO | 크리틱 없는 그룹 상대 RL(DeepSeekMath→R1) — 2025~26 reasoning 튜닝 표준 | [arXiv:2402.03300](https://arxiv.org/pdf/2402.03300) |
| 보안 도메인 RL | Minerva: CTI LLM에 RLVR(검증 가능 보상) 적용 사례 | [arXiv:2602.00513](https://arxiv.org/pdf/2602.00513) |

#### Distillation / Continual Learning

- 지식 증류 서베이: [arXiv:2402.13116](https://arxiv.org/pdf/2402.13116)
- LLM 지속학습 서베이(CSUR 2025): [Wang-ML-Lab/llm-continual-learning-survey](https://github.com/Wang-ML-Lab/llm-continual-learning-survey) — F10 continual FT 의 망각 완화 전략
- Post-training 전반 서베이(2025): [arXiv:2503.06072](https://arxiv.org/pdf/2503.06072)
- 망각 대응: Self-Distillation 성능 회복([arXiv:2604.15794](https://arxiv.org/pdf/2604.15794)), 도메인 보존 멀티티처 on-policy 증류([arXiv:2605.27115](https://arxiv.org/pdf/2605.27115)) — 보안 특화 튜닝 후 일반능력 회귀 검사(§5 게이트)와 직결

### 2.2 데이터셋 구축·정제·출처추적

#### 합성 데이터 생성

| 기법 | 핵심 내용 | 링크 |
|---|---|---|
| Self-Instruct | 소량 시드에서 instruction 부트스트랩 — 합성 데이터 원조 | 정리: [arXiv:2503.06072](https://arxiv.org/pdf/2503.06072) |
| Evol-Instruct / Tag-Evol | 명령 복잡도 자동 진화(WizardLM 계열) | [Tag-Evol arXiv:2505.24165](https://arxiv.org/pdf/2505.24165) |
| Magpie (ICLR 2025) | 정렬 LLM에서 무시드 400만 instruction 자동 추출 | [arXiv:2406.08464](https://arxiv.org/abs/2406.08464v2) · [Magpie-Align HF](https://huggingface.co/Magpie-Align) |
| CoT-Self-Instruct | 추론 포함 고품질 합성(2025) | [arXiv:2507.23751](https://arxiv.org/pdf/2507.23751) |
| **CyberPal.AI** | 전문가 주도 **보안 instruction 합성 프레임워크** — F10/§7.4 직접 참고 | [arXiv:2408.09304](https://arxiv.org/pdf/2408.09304) |

#### Curation / Dedup / Decontamination

- 오염 탐지 서베이: [arXiv:2410.18966](https://arxiv.org/pdf/2410.18966)
- 13-gram 디컨탬(HF DataTrove 구현)이 실무 표준 — train/test 누수 방지(§7.3 ⑥⑧) 고도화 근거 (사례: [arXiv:2502.10361](https://arxiv.org/pdf/2502.10361))
- 도메인 분류 기반 큐레이션: [arXiv:2502.10341](https://arxiv.org/pdf/2502.10341)
- 동적 벤치마크(오염 회피): VarBench [arXiv:2406.17681](https://arxiv.org/pdf/2406.17681)

#### 출처·라이선스·Provenance — F14(출처 필수 명기)의 학술·산업 근거

- **Data Provenance Initiative**: 1,800+ 데이터셋 라이선스·귀속 감사 — 라이선스 60%+ 오분류, 70%+ 미명시 발견. **F14 메타데이터 스키마(라이선스·창작자·계보) 벤치마크로 채택 권장** — [arXiv:2310.16787](https://arxiv.org/pdf/2310.16787) · [Nature MI](https://www.nature.com/articles/s42256-024-00878-8)
- Foundation Model Transparency Index 2024: [arXiv:2407.12929](https://arxiv.org/pdf/2407.12929)
- 검증 가능 파인튜닝(ZK 학습 증명, 2025): [arXiv:2510.16830](https://arxiv.org/pdf/2510.16830) — 규제 환경 감사 대응 최전선

### 2.3 보안(사이버시큐리티) 특화 LLM

#### 모델

| 모델 | 핵심 내용 | 링크 |
|---|---|---|
| **Foundation-Sec-8B** (Cisco) | Llama 3.1 8B + 보안 코퍼스 5.1B 토큰 지속 사전학습. Base/Instruct/Reasoning 3종(최초 오픈 보안 추론 모델) | [HF Base](https://huggingface.co/fdtn-ai/Foundation-Sec-8B) · [Instruct](https://huggingface.co/fdtn-ai/Foundation-Sec-8B-Instruct) · [Reasoning](https://huggingface.co/fdtn-ai/Foundation-Sec-8B-Reasoning) · [기술보고서](https://arxiv.org/pdf/2508.01059) · [Cisco 블로그](https://blogs.cisco.com/security/foundation-sec-cisco-foundation-ai-first-open-source-security-model) |
| **Llama-Primus** (Trend Micro) | 사전학습(Primus-Seed)→SFT(Primus-Instruct)→추론 증류(Primus-Reasoning) 전 단계 오픈 — **SecuFTPL 과 가장 유사한 공개 파이프라인 레퍼런스** | [arXiv:2502.11191](https://arxiv.org/abs/2502.11191) · [HF Llama-Primus-Base](https://huggingface.co/trend-cybertron/Llama-Primus-Base) |
| WhiteRabbitNeo → DeepHat | 언센서드 레드팀/펜테스팅 모델(방어 목적 참고만 — PRD Out of Scope 경계) | [HF WhiteRabbitNeo](https://huggingface.co/WhiteRabbitNeo) · [DeepHat-V1-7B](https://huggingface.co/DeepHat/DeepHat-V1-7B) · [deephat.ai](https://www.deephat.ai/) |
| Lily-Cybersecurity-7B | Mistral-7B + 수작업 22K 보안 Q&A(A100 1장, 24h) — 소규모 SFT 사례 | [HF segolilylabs/Lily-Cybersecurity-7B-v0.2](https://huggingface.co/segolilylabs/Lily-Cybersecurity-7B-v0.2) |
| RedSage (2026) | 보안 필터링 코퍼스 CPT + 큐레이션/증강 post-training | [arXiv:2601.22159](https://arxiv.org/pdf/2601.22159) |

#### 보안 벤치마크 — 리더보드(F1)·평가지표 가이드(F12) 구성 후보

| 벤치마크 | 핵심 내용 | 링크 |
|---|---|---|
| **CTIBench** (NeurIPS'24 Spotlight) | CTI 지식·CVE/CWE 근본원인·CVSS 예측·ATT&CK 추출·행위자 귀속 5과제 4,610문항 — **SecuFTPL §5 지표(attack_f1/severity)와 정합** | [arXiv:2406.07599](https://arxiv.org/abs/2406.07599) · [GitHub](https://github.com/aiforsec/cti-bench) |
| SecBench (Tencent+PolyU) | 9개 하위도메인 MCQ 44,823 + SAQ 3,087 (중/영) — 최대 규모 | [arXiv:2412.20787](https://arxiv.org/abs/2412.20787) · [GitHub](https://github.com/secbench-git/SecBench) |
| CyberSecEval 4 (Meta PurpleLlama) | 보안 능력+위험(불안전 코드·프롬프트 인젝션) 종합 스위트 | [GitHub](https://github.com/meta-llama/PurpleLlama/tree/main/CybersecurityBenchmarks) · [문서](https://meta-llama.github.io/PurpleLlama/CyberSecEval/docs/intro) · [v2 논문](https://arxiv.org/html/2404.13161) |
| CyberSOCEval (2025) | 멀웨어 분석·위협인텔 추론 SOC 실무 벤치마크 | [arXiv:2509.20166](https://arxiv.org/pdf/2509.20166) |
| CAIBench (2025) | 보안 AI 에이전트 평가 메타벤치마크 | [arXiv:2510.24317](https://arxiv.org/pdf/2510.24317) |
| 총정리 | Awesome-AI-Security-Benchmarks | [GitHub](https://github.com/EvanThomasLuke/Awesome-AI-Security-Benchmarks/blob/main/README.md) |

#### 보안 instruction 데이터셋

- Primus 컬렉션(사전학습+SFT+추론 증류 전부 공개): [arXiv:2502.11191](https://arxiv.org/abs/2502.11191) · [HF papers](https://huggingface.co/papers/2502.11191)
- CTI-HAL(사람 주석 CTI 분석): [arXiv:2504.05866](https://arxiv.org/pdf/2504.05866)
- CyberPal.AI 전문가 주도 instruction: [arXiv:2408.09304](https://arxiv.org/pdf/2408.09304)

### 2.4 파인튜닝 도구·프레임워크 시장

| 도구 | 2025~26 상태 | 링크 |
|---|---|---|
| Unsloth | 단일 GPU 속도/메모리 최강(A100 40GB Llama-3.1-8B: 3.2h vs Axolotl 5.8h). 2026.2: MoE 12배 가속·임베딩·초장문 RL | [비교 1](https://theaiengineer.substack.com/p/unsloth-vs-axolotl-vs-llama-factory) · [비교 2](https://www.spheron.network/blog/axolotl-vs-unsloth-vs-torchtune/) |
| Axolotl | v0.8.x 프로덕션 성숙: 시퀀스 병렬(장문)·QAT·GRPO·리워드 모델링 — 멀티 GPU 1순위 | [2026 비교](https://dev.to/ultraduneai/eval-003-fine-tuning-in-2026-axolotl-vs-unsloth-vs-trl-vs-llama-factory-2ohg) |
| LLaMA-Factory | Unsloth 백엔드 시 네이티브 대비 6% 이내 — GUI+성능 동시 확보 | [Modal 비교](https://modal.com/blog/fine-tuning-llms) |
| ms-swift (AAAI 2025) | 600+ LLM·300+ MLLM CPT/SFT/DPO/GRPO — 최다 모델 커버리지 | [GitHub](https://github.com/modelscope/ms-swift) · [arXiv:2408.05517](https://arxiv.org/html/2408.05517v4) |
| torchtune | PyTorch 네이티브·QAT·훈련 루프 제어 극대화 | [arXiv:2605.21442](https://arxiv.org/pdf/2605.21442) |
| HF TRL/PEFT | TRL=GRPO 포함 RL 표준, PEFT=DoRA 등 변형 흡수 | [PEFT Releases](https://github.com/huggingface/peft/releases) |

핵심 관찰: 기능 격차 소멸(전부 LoRA/QLoRA/DPO/GRPO 지원) — 차별화 축은 **속도(Unsloth) · 멀티GPU/장문(Axolotl) · 모델 커버리지(ms-swift) · 제어권(torchtune)**.

상용 API: OpenAI SFT/DPO/**RFT** 3종([DPO 가이드](https://developers.openai.com/cookbook/examples/fine_tuning_direct_preference_optimization_guide) · [RFT 문서](https://developers.openai.com/api/docs/guides/reinforcement-fine-tuning)), Fireworks SFT/DPO+RFT([발표](https://fireworks.ai/blog/reinforcement-fine-tuning) · [가격](https://fireworks.ai/pricing)) — 시장 방향 = "SFT → DPO → 검증가능 보상 RFT" 3단 상품화.

### 2.5 평가·검증

- lm-evaluation-harness: Open LLM Leaderboard 백본, 60+ 태스크 — [GitHub](https://github.com/EleutherAI/lm-evaluation-harness)
- LightEval(HF): 1,000+ 태스크, vLLM/SGLang 백엔드 — SecuFTPL vLLM 경로와 정합 ([평가 플랫폼 비교](https://latitude.so/blog/open-source-platforms-llm-evaluation))
- LLM-as-Judge 표준화·편향 보정: FairJudge [arXiv:2602.06625](https://arxiv.org/pdf/2602.06625) · [DeepEval 블로그](https://deepeval.com/blog/llm-as-a-judge)
- 구조화 출력 평가:
  - JSONSchemaBench — 실세계 JSON 스키마 10K로 constrained decoding 6종 평가: [arXiv:2501.10868](https://arxiv.org/abs/2501.10868) · [GitHub](https://github.com/guidance-ai/jsonschemabench)
  - Structured Output Benchmark — 문법 유효성 아닌 **값 정확도** 평가. 문법 제약 디코딩이 의미 열화 유발 가능: [arXiv:2604.25359](https://arxiv.org/pdf/2604.25359)
  - **시사점**: SecuFTPL §5 `json_valid_rate` 단독으로는 부족 — "스키마 유효성 + 값 정확도" 2축 평가 필요.

### 2.6 시장 동향 — 도메인 특화 sLLM·온프레미스·규제

- SLM 시장: 2025 ~$1.3B → 2035 $16.2B(CAGR 32.1%), "모델 학습·파인튜닝"이 최고 성장 세그먼트 — [MarketsandMarkets](https://www.marketsandmarkets.com/Market-Reports/small-language-model-market-4008452.html) · [GM Insights](https://www.gminsights.com/industry-analysis/small-language-models-market) · [Polaris](https://www.polarismarketresearch.com/industry-analysis/small-language-model-market)
- 온프레미스 드라이버 = 규제·프라이버시, 최대 지출처 = 금융·의료 — [MarketsandMarkets 블로그](https://www.marketsandmarkets.com/blog/ICT/small-language-model-market)
- 국내 금융권: 망분리 규제 → 온프레미스 sLLM 확산(미래에셋증권-네이버클라우드 사례) — [CIO Korea](https://www.cio.com/article/3538247/%EB%84%A4%EC%9D%B4%EB%B2%84%ED%81%B4%EB%9D%BC%EC%9A%B0%EB%93%9C-%EB%AF%B8%EB%9E%98%EC%97%90%EC%85%8B%EC%A6%9D%EA%B6%8C-%EC%98%A8%ED%94%84%EB%A0%88%EB%AF%B8%EC%8A%A4-%ED%99%98%EA%B2%BD%EC%97%90.html) · [메타넷글로벌](https://metanetglobal.com/bbs/board.php?bo_table=tech&wr_id=101)
- 공공부문: 공공 AX용 sLLM 도입 프레임워크 연구(RAG+온프레미스+LoRA) — [KCI 논문](https://www.kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART003274990)
- 보안 도메인 신호: Cisco·Trend Micro·Meta 가 보안 특화 오픈 모델/데이터/벤치마크 직접 공개 — "로컬 배포 가능한 보안 LLM"이 벤더 전략 축

## 3. SecuFTPL 적용 제언 (스타 분석 §1 + 동향 조사 §2 종합)

| 우선순위 | 제언 | 근거 |
|---|---|---|
| P0 | 실학습 백엔드: **Unsloth(CUDA) + mlx-lm LoRA(Apple Silicon)** 이원화, rsLoRA/DoRA 토글 옵션 | §1.1·§2.1·§2.4 — 시뮬레이션→실전환 경로. mlx-lm 은 이미 F11 의존성 |
| P0 | 안전 거부 데이터: **jailbreak_llms** 를 safety_refusal task 로 수입(F6 어댑터) | §1.6 — PRD 안전성 ~10% 혼합의 실데이터 원천 |
| P0 | 베이스모델 후보에 **Foundation-Sec-8B·Llama-Primus** 등 보안 특화 모델 등록(F2 카탈로그) | §2.3 — 범용 모델 대비 보안 지속학습 이점, Primus 는 파이프라인 전체 공개 레퍼런스 |
| P0 | 리더보드 표준 벤치 연동: **CTIBench**(+CyberSecEval 4) — §5 attack_f1/severity 와 정합 | §2.3 — 자사 평가셋과 공개 벤치 병행으로 기준선 신뢰 확보 |
| P1 | 선호학습 확장: 만족도 👍/👎(binary) → **KTO**(쌍 불필요) 우선, 이후 ORPO/GRPO(RLVR: CVSS·ATT&CK 정답 검증 보상) | §2.1 — 현 DPO-pairs export 보다 환류 데이터 구조와 KTO 가 더 정합 |
| P1 | 문서 파싱 업그레이드: pypdf → **docling 또는 marker**(표·레이아웃 보존), 스캔 문서는 surya | §1.3 — CTI/취약점 보고서 표(IOC·CVSS) 손실 방지 |
| P1 | 정제 게이트 ⑥⑧ 고도화: **13-gram 디컨탬(DataTrove 방식)** 내장 — train/test 누수·벤치 오염 방지 | §2.2 |
| P1 | F14 출처 스키마를 **Data Provenance Initiative** 메타데이터(라이선스·창작자·계보)와 정렬 | §2.2 — 라이선스 오분류 60%+ 현실에서 감사 가능성 확보 |
| P1 | 평가 하네스: **lm-evaluation-harness/LightEval 태스크 YAML** 호환 + 구조화 출력 2축(스키마 유효성+값 정확도) 평가 | §1.4·§2.5 — json_valid_rate 단독 한계 보완 |
| P1 | RAG 합성 고도화: **GraphGen**(지식 커버리지)·CyberPal.AI(전문가 주도)·Magpie 방식 도입 검토 | §1.2·§2.2 — F10 합성 QA 품질 |
| P2 | 검수 큐 → **Label Studio 연동(export/import)** 옵션 | §1.2 — 대규모 외주/다중 검수자 |
| P2 | 양자화 옵션: llm-compressor(AWQ/GPTQ)·SINQ 를 §7.14 변환 표에 추가 | §1.5 — 변환 후 스모크 평가와 결합 |
| P2 | continual FT(F10) 회귀 검사에 **망각 완화 기법**(self-distillation 회복 등) 반영 | §2.1 — 보안 특화 후 일반능력 유지 |

**시장 포지셔닝**: 국내 금융 망분리·공공 AX 의 온프레미스 sLLM 수요(§2.6)가 SecuFTPL 의 직접 시장 —
경쟁·참조 지점은 Llama-Primus(공개 파이프라인)와 Foundation-Sec(로컬 배포 보안 모델). PRD govtech/finance
오버레이(에어갭 manifest·감사로그)가 그대로 차별화 요소.

## 참고 — 조사 방법

- 스타 분석: `pub-star-classifier` 출력에서 FT 관련 정규식 필터(fine-tune/LoRA/QLoRA/PEFT/SFT/DPO/
  dataset/synthetic/quantize/eval/annotation 등) → 수작업 선별·단계 매핑. 이미지/비전 전용 라벨링
  도구(CVAT·labelme 등 다수)는 텍스트 파이프라인과 무관하여 제외(Label Studio 만 멀티타입이라 포함).
- 동향 조사: WebSearch 기반(§2), 링크는 검색 확인된 것만 기재.
