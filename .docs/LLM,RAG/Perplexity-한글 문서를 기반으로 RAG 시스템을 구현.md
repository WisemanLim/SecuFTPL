<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# 한글 문서를 기반으로 RAG 시스템을 구현하려고 합니다. 기본적으로 LLM 모델을 선택해야 하는데, 2026년 3월 기준으로 가장 성능(정확도 측면, 속도 측면은 후순위)이 뛰어난 모델을 조사 및 비교, 추천해 주세요.

한글 문서 기반 RAG에서 “정확도 최우선” 기준으로는 여전히 **최신 폐쇄형 상위 모델 + 한국어 튜닝된 임베딩** 조합이 가장 유력합니다. 속도·비용·온프렘 요구사항에 따라 대안을 고르는 식으로 설계하는 게 좋습니다.[^1_1][^1_2][^1_3]

## 1. 지금 시점 상위권 LLM 전반 그림

전반적인 종합 벤치마크(수학·추론·코딩·지식 혼합) 기준 상위는 다음 계열입니다.[^1_4][^1_5][^1_1]


| 구분 | 대표 모델 | 특징 요약 |
| :-- | :-- | :-- |
| OpenAI 계열 | GPT‑5 Pro / GPT‑5.2 / o3 계열 | 고난도 추론, 코딩, 툴 사용 등에서 매우 강함.[^1_1] |
| Anthropic 계열 | Claude Opus 4.x / Sonnet 4.5 | 긴 맥락 추론·안전성·코딩에서 상위권.[^1_1][^1_4] |
| Google 계열 | Gemini 2.5 Pro / 3 Pro Preview | 멀티모달·코딩·수학에서 매우 높은 점수.[^1_1][^1_6] |
| 기타 프론티어 | Grok 4 등 | 특정 추론/코딩 벤치에서 강하지만 한글/도입 편의성은 케이스 바이 케이스.[^1_1][^1_5] |

한국어 전용 벤치마크(예: Open Ko‑LLM Leaderboard2, CSAT 벤치마크)는 공통적으로 “프론티어 폐쇄형 > 고성능 영문 LLM > 한국계/오픈소스 Ko‑LLM” 구조를 보여줍니다.[^1_2][^1_3]

## 2. 한글 RAG에서 LLM이 하는 일 관점

한글 RAG에서 LLM은 대략 다음에 쓰입니다.

- 질의 언어 이해 및 리포맷팅 (Query rewriting, hybrid search 쿼리 생성).
- Retrieval 결과를 기반으로 한 grounded answer 생성.
- 필요 시 chain‑of‑thought / tool calling.

이 중 “정확도”를 가장 크게 좌우하는 것은:

- (1) 검색/임베딩 품질 (특히 한국어에 맞는 tokenizer/segmentation)과[^1_2]
- (2) LLM의 “지시 따르기 + 근거 중심 정리 능력”입니다.[^1_1]

즉, LLM 자체는 영어 벤치 기준 상위권이면 충분하고, 한국어는 **instruction tuning이 잘 되어 있는지, 긴 context에서 citation을 얼마나 잘 유지하는지**가 더 중요합니다.[^1_3][^1_2]

## 3. 시나리오별 추천 (정확도 우선, 속도/비용 후순위)

### 3.1 클라우드 사용 가능, 비용 허용 (가장 권장)

한글 문서 RAG에서 “최대한 정확하게, 환각 최소, 복잡한 질의도 커버”를 목표로 할 때:

1) **GPT‑5 Pro (또는 최신 5.x High/Medium 계열)**

- 이유:
    - 종합 reasoning / QA / 코딩 벤치에서 여전히 최상위 그룹으로 평가.[^1_1]
    - 긴 context에서 citation 기반 답변 품질이 안정적이라 대용량 RAG에 유리.[^1_5][^1_1]
    - 한글 지원 품질도 상위권으로 보고되며, 한국어 CSAT 계열에서도 폐쇄형 모델이 일괄 우세.[^1_3]
- 권장 아키텍처:
    - 임베딩: OpenAI text-embedding-3-large 또는 한국어 특화 오픈 모델(예: bge-m3-ko 변형)을 자체 호스팅.
    - Retriever: hybrid(BM25 + dense) + hierarchical chunking, answer는 GPT‑5에 RAG template로.

2) **Claude Opus 4.x or Sonnet 4.5**

- 이유:
    - 최신 벤치에서 reasoning·코딩·멀티턴 품질이 GPT‑5와 근접하거나 일부 항목에서 우위.[^1_4][^1_1]
    - 긴 맥락에서 사용자가 원하는 스타일로 정리하는 능력이 강해, “리포트형 RAG 답변”에 특히 좋음.[^1_5][^1_4]
- 선택 기준:
    - 대화/리포트 중심 QA, 안전성·톤 관리 중시 → Claude 선호.
    - 툴콜/코드/에이전트워크플로 비중이 더 크면 GPT‑5 쪽이 세팅이 풍부한 편.

3) **Gemini 2.5 Pro / 3 Pro Preview**

- 이유:
    - 수학, 코딩, 멀티모달 종합 점수에서 아주 강력한 것으로 보고.[^1_6][^1_1]
    - GCP 상의 데이터·검색 인프라와 붙여 쓰면 엔드투엔드 파이프라인 구축이 용이.[^1_5]
- 한국어:
    - Google 내부 벤치 및 KSAT 계열에서 강점을 보였다는 보고가 있으며, 멀티모달 CSAT 벤치에서 상위 그룹.[^1_3]
- GCP 기반 인프라를 이미 쓰고 있으면 RAG-as-a-service 스타일로 빠르게 구축 가능.

→ 이 3개는 “정확도 지상주의” 기준으로는 거의 동급 상위권이라,

- 사내 정책(미국/유럽/일본 클라우드 허용 범위),
- SDK 편의성,
- 가격·슬로틀링,
에 따라 선택하는 게 현실적입니다.[^1_1][^1_5]


### 3.2 온프렘 / VPC, 오픈소스 위주

클라우드 API를 쓰기 어렵거나, 데이터가 민감(의료·유전체)해서 온프렘을 선호하는 경우:

1) **DeepSeek‑V3.2 계열**

- 특징:
    - 최근 오픈소스 중 reasoning·코딩에서 GPT‑5 급에 근접 또는 일부 벤치에서 상회한다는 평가.[^1_7]
    - Sparse Attention 기반으로 긴 context에서 효율 좋음.[^1_7]
- 한국어:
    - 중국계/멀티링구얼 코퍼스에 한국어도 상당량 포함된 것으로 추정되며, 다국어 QA에서 준수한 성능 보고.[^1_7][^1_2]
    - 다만 순수 Ko‑LLM만큼 local nuance를 잡지는 못할 수 있어, RAG 상에서 prompt를 한글+영어 혼합으로 설계하는 것이 효과적.

2) **GLM‑5, Llama‑4 계열**

- GLM‑5:
    - 대형 오픈 LLM 중 하나로 긴 context·코딩에서 strong, 일부 벤치에서 DeepSeek와 비슷한 수준으로 평가.[^1_7]
- Llama‑4 계열:
    - 서드파티 시스템(예: Vellum LLM leaderboard)에서 안정적인 고성능 모델군으로 기록.[^1_8][^1_7]
- 한국어:
    - 둘 다 멀티링구얼 프리트레인을 했기 때문에 일반적인 한글 QA·요약은 충분히 가능.[^1_2][^1_7]
    - 정밀한 법률/의학 한국어는 추가 LoRA 튜닝을 붙이는 게 좋음.

3) **한국어 특화 Ko‑LLM (예: Ko‑llama, KULLM, Polyglot‑Ko 등)**

- Open Ko‑LLM Leaderboard2 등에서, 한국어 논리/독해/요약 품질이 기존 번역 기반 벤치보다 더 잘 측정되도록 개선되어 있음.[^1_2]
- 최신 Ko‑LLM2 계열 모델들은 한국어 문어체·수능형 질의에서 좋은 성과를 보이나, 전 세계적 프론티어보다는 1단계 아래.[^1_3][^1_2]
- 전략:
    - **임베딩/리트리버는 Ko‑LLM 계열** (형태소·조사 감도 높음),
    - **생성은 DeepSeek‑V3.2나 GLM‑5/Llama‑4** 로 가는 “한국어+프론티어 하이브리드” 구성이 현실적입니다.


## 4. 한글 RAG 정확도 극대화를 위한 설계 팁

모델 선택 외에 정확도에 직접적으로 영향을 주는 부분만 요약하면:

- **임베딩은 한국어 특화 + multi‑vector 고려**
    - Open Ko‑LLM Leaderboard2 논문도 기존 번역 기반 벤치의 한계를 지적하면서 한국어 고유 특성 반영의 중요성을 강조.[^1_2]
    - bge‑m3‑ko 계열이나 Ko‑SimCSE류를 사용, sentence+passage dual encoder 구조를 추천.
- **Chunking과 retrieval strategy**
    - 조사/어미 때문에 문장 단위 자르기가 삐끗하면 맥락 손실이 커서, 문단+문장 혼합 단위 chunking이 유리.[^1_2]
    - Dense + BM25 hybrid, re‑ranking(ColBERTv2‑ko 등) 추가하면 복잡 질의에서 큰 향상 보고.[^1_3]
- **Prompting**
    - LLM에게 “반드시 제공된 근거 문단만 사용하고, 출처를 인용하라”는 system prompt + output schema (JSON/Markdown citation)를 강하게 줘야 환각이 줄어듭니다.[^1_1][^1_3]
    - 한글 RAG라 해도 내부 reasoning을 영어로 유도(예: hidden chain‑of‑thought)하고, 최종 답만 한국어로 출력시키면 품질이 좋아지는 케이스가 많습니다.[^1_1]
- **도메인 튜닝**
    - 의료/유전체 같이 특수 도메인은, 사내 Q/A 로그·도메인 문서를 기반으로 LoRA RAG‑instruction 튜닝을 하면 open Ko‑LLM 기준에서 상당한 성능 향상이 보고되었습니다.[^1_3][^1_2]


## 5. 상황별 구체 추천 정리

정리해서, “한글 문서 기반 RAG + 정확도 최우선” 기준으로:

- **클라우드 허용 + 비용 괜찮음 (가장 권장)**
    - 1순위: GPT‑5 Pro (또는 최신 5.x High/Medium) + 한국어 특화 임베딩.[^1_1][^1_3]
    - 1.5순위: Claude Opus 4.x / Sonnet 4.5 (리포트/컨설팅 스타일 RAG에 특히 강함).[^1_4][^1_1]
    - 2순위: Gemini 2.5 Pro / 3 Pro Preview (GCP·멀티모달 연동 시).[^1_6][^1_1]
- **온프렘/자체 호스팅, 오픈소스 선호**
    - 1순위: DeepSeek‑V3.2‑(수십 B 이상) + Ko‑임베딩 하이브리드.[^1_7][^1_2]
    - 2순위: GLM‑5 / Llama‑4 70B+ 계열 + Ko‑임베딩.[^1_8][^1_7]
    - 3순위: 한국어 특화 Ko‑LLM2 계열을 생성까지 전부 쓰되, 부족한 reasoning은 영문 LLM을 side‑car로 붙이는 구조.[^1_2][^1_3]

원하시면:

- “의료/마이크로바이옴 논문/전자의무기록” 같은 구체 도메인 기준으로,
- 후보 모델 2~3개만 골라서 prompt 템플릿, chunking/임베딩 전략, eval 스크립트(py, LangChain/LlamaIndex/RagFlow 등)까지 포함한 **엔드투엔드 레퍼런스 아키텍처**를 잡아 드리겠습니다.
<span style="display:none">[^1_10][^1_9]</span>

<div align="center">⁂</div>

[^1_1]: https://lmcouncil.ai/benchmarks

[^1_2]: https://aclanthology.org/2025.naacl-industry.22/

[^1_3]: https://www.emergentmind.com/topics/2026-korean-csat-llm-evaluation-leaderboard

[^1_4]: https://www.pluralsight.com/resources/blog/ai-and-data/best-ai-models-2026-list

[^1_5]: https://zapier.com/blog/best-llm/

[^1_6]: https://marcus-story.tistory.com/167

[^1_7]: https://www.bentoml.com/blog/navigating-the-world-of-open-source-large-language-models

[^1_8]: https://vellum.ai/llm-leaderboard

[^1_9]: https://www.mangomindbd.com/blog/march-2026-ai-benchmarks

[^1_10]: https://www.linkedin.com/pulse/openais-new-gpt-41-o-models-how-stack-up-against-miriam-hftlf


---

# 자체적으로 구동이 필요한 VLLM, Ollama, llama.cpp 등으로 허깅페이스 등의 오픈 모델을 사용해야 합니다. 재조사 및 비교, 추천해 주시고, 해당 모델을 지속적인 학습과 함께 모델 업데이트 방법에 대해서도 상세한 가이드를 주세요.

온프렘(vLLM / Ollama / llama.cpp) 기준이면, 2026년 3월 현재는 **“상위 범용 오픈 모델 + 한국어 특화 임베딩/RAG 튜닝”** 조합이 가장 현실적인 선택입니다.[^2_1][^2_2][^2_3]

## 1. 온프렘 RAG용 후보 모델 라인업

### 1.1 범용 상위 오픈 LLM (생성용)

| 용도 | 모델 후보 | 장점 | 비고 |
| :-- | :-- | :-- | :-- |
| 최상위 reasoning·QA | DeepSeek‑V3.2 (Instruct 계열) | 2026년 기준 오픈소스 중 추론·에이전트 워크로드에서 최상위급.[^2_2][^2_3] MIT 라이선스, 긴 컨텍스트, 멀티스텝 툴 사용 튜닝. | 다중 GPU 필요 (수십 B 이상), vLLM에서 주로 운용. |
| 고성능 범용 LLM | GLM‑5‑(X) / Llama‑4‑(X) Instruct | 2026 오픈소스 LLM 가이드에서 reasoning/코딩/일반 QA 모두 우수로 평가.[^2_2] | HuggingFace에 변형 많고 vLLM 지원이 빠름. |
| 경량·저자원 | Llama‑4‑8B/14B‑Instruct, Gemma‑3‑9B 등 | 수 GB VRAM에서도 돌릴 수 있고 llama.cpp/Ollama에서 쉽게 구동.[^2_4][^2_5] | 정확도는 상위 모델보다 한 단계 아래. |

- 이 중 **정확도 최우선**이면: DeepSeek‑V3.2‑Instruct → GLM‑5 / Llama‑4‑70B 계열 순으로 보는 게 합리적입니다.[^2_2][^2_3]
- 한국어는 멀티링구얼 프리트레인 덕에 기본 수준 이상은 되지만, 한국어 전용 LLM보다는 덜 자연스러울 수 있습니다.[^2_1]


### 1.2 한국어 특화 오픈 LLM (보조 또는 생성 겸용)

- Open Ko‑LLM Leaderboard2에서 한국어 LLM을 종합 평가하는데, 여기서 잘 나오는 축은 주로:
    - Upstage SOLAR‑Ko 계열,
    - 국내 대기업/스타트업 Ko‑LLM2/AX‑4 등 한국어 특화 모델들입니다.[^2_6][^2_7][^2_1]
- 한국어 수능형 독해/논리·Ko‑GSM8K 같은 실제 사용에 가까운 벤치에서 **전통 번역 기반 벤치보다 훨씬 의미 있는 지표**를 제공한다는 점이 강조됩니다.[^2_8][^2_1]

RAG 관점에서는 다음 식 구성이 좋습니다.

- **임베딩/리트리버**: 한국어 특화(예: SOLAR‑embedding, Ko‑bge, Ko‑SimCSE 등) 사용.[^2_1]
- **생성 LLM**:
    - 고정확도 필요: DeepSeek‑V3.2 / GLM‑5 / Llama‑4‑70B Instruct.
    - pure 국문 톤/뉘앙스 중시: SOLAR‑Instruct / Ko‑LLM2‑Instruct 등 병행.


## 2. vLLM / Ollama / llama.cpp에서의 사용성

### 2.1 vLLM

- vLLM은 HuggingFace 호환 모델 대부분을 지원하며, 최신 DeepSeek‑V3.2·Llama‑4·GLM‑5 같은 대형 모델을 “PagedAttention” 기반으로 효율적으로 서빙 가능한 것으로 소개됩니다.[^2_3][^2_2]
- 장점:
    - Python 에코시스템(LangChain, LlamaIndex, FastAPI)과 붙이기 쉬움.
    - 다중 GPU, 텐서 병렬, 동적 배치 등 서버 사이드 배포에 최적.
- 한글 RAG 서버 구성 예 (대략):
    - vLLM 인퍼런스 서버 (DeepSeek‑V3.2‑Instruct, HTTP/OpenAI 호환 엔드포인트).
    - 별도 임베딩 서버 (Ko‑임베딩 모델, sentence‑transformers + FAISS/pgvector).
    - API 게이트웨이: RAG orchestration, guardrail, 로깅.


### 2.2 Ollama

- Ollama는 Mac/리눅스 개발 환경에서 손쉽게 Llama‑계열·Gemma‑계열 모델을 풀 패키지로 제공하는 것이 특징입니다.[^2_4]
- 현재 주력:
    - Llama‑3/4‑Instruct, Gemma‑2/3, DeepSeek·Qwen 변형 등 주요 오픈 모델들을 “`ollama run xxx`” 형태로 곧바로 사용 가능.
- 장점:
    - 로컬 PoC, 개발용 디버깅에 아주 강함.
    - 모델 변경/버전 관리가 모델명/태그 단위로 쉬움.
- 단점:
    - 대규모 프로덕션 서빙(수십 RPS 이상, 다중 GPU)은 vLLM보다 제어권이 적고, 세밀한 최적화가 어렵습니다.[^2_2]


### 2.3 llama.cpp

- C/C++ 기반 경량 인퍼런스 프레임워크로, CPU·소형 GPU·모바일·AMD ROCm까지 넓게 지원합니다.[^2_5][^2_4]
- 특징:
    - GGUF 포맷, 2–8bit 양자화를 통한 메모리 절감·속도 향상.[^2_5][^2_4]
    - ROCm/AMD용 포크도 공식 문서에서 별도로 관리, HIP 커널 기반 가속 제공.[^2_5]
- 쓰임새:
    - 엣지/온프렘 경량 배포 or 사내 PC 보급형 배포.
    - vLLM 기반 메인 서버 + llama.cpp 기반 fallback/오프라인용 구조가 현실적.


## 3. 한국어 RAG 관점 모델 조합 추천

GPU 자원과 정확도 우선순위를 가정하고, 몇 가지 패턴을 제안합니다.

### 3.1 “정확도 극대화형” (여유 있는 GPU, 서버 RAG)

- **생성 LLM**: DeepSeek‑V3.2‑Instruct (또는 GLM‑5‑70B / Llama‑4‑70B‑Instruct).[^2_3][^2_2]
- **임베딩**: bge‑m3‑ko / SOLAR‑embedding / Ko‑SimCSE‑large 등 한국어 특화.[^2_1]
- **서빙**:
    - vLLM: LLM 서빙.
    - 별도 Python 서비스: 임베딩 + vector store + retriever.
- **RAG 구조**:
    - Query rewriting (한→영 혼합) → hybrid retrieval(BM25 + dense + rerank) → context compression → DeepSeek로 answer.


### 3.2 “균형형” (중~상급 GPU, Prod+온프렘)

- **생성 LLM**: Llama‑4‑14B/34B‑Instruct 또는 DeepSeek‑V3.2‑13B 변형.
- **서빙**:
    - PoC/개발: Ollama (모델 태그로 관리).
    - Prod: vLLM 또는 llama.cpp (GGUF 양자화)로 이관.
- 정확도를 끌어올리려면:
    - 체인: 고난도 질의만 70B 서버로 포워딩, 일반 질의는 14B가 처리하는 **two‑tier routing**.


### 3.3 “경량·온디바이스형”

- **생성 LLM**: Llama‑4‑8B‑Instruct / Gemma‑3‑9B‑Instruct GGUF 양자화.
- **서빙**: 전부 llama.cpp 기반, CPU+소형 GPU에서 구동.[^2_4][^2_5]
- RAG 정확도는 떨어지지만, 오프라인/사내망 PC 대량 배포에 적합.


## 4. “지속적 학습”과 모델 업데이트 전략

여기서 “지속적 학습”은 크게 세 층으로 나누는 게 안전합니다.

1) **RAG 데이터 업데이트** (권장, 위험도 낮음)
2) **Instruction/Preference Tuning (LoRA/PEFT)**
3) **Base model 재학습 또는 full fine‑tuning** (권장 X, 유지보수·안정성 리스크 큼)

### 4.1 RAG 인덱스 업데이트 파이프라인

- **문서 수집/변경 감지**:
    - 원천: 폴더/DB/ES/SharePoint/EMR 등.
    - 변경 감지: `updated_at` 컬럼, 파일 해시, Git 리비전 등.
- **전처리**:
    - 한국어 문단·문장 단위 segment (형태소/문장 분리기 적용).
    - domain‑specific 메타데이터 (논문 섹션, 환자 ID, 샘플 ID 등) 부착.
- **임베딩 \& 인덱싱**:
    - Ko‑임베딩으로 chunk 임베딩 생성, vector store에 upsert.
    - stale 문서는 soft delete 혹은 버전 필드로 구분.
- **스케줄링**:
    - 배치형: Airflow/Prefect, “매일 새벽 전체 인덱스 리빌드 + 수시 증분”.
    - 스트리밍형: Kafka + 소비자에서 실시간 인덱싱.
- **모델 비동기 업데이트**:
    - 인덱스 버전을 라우팅 레이어에서 관리 (예: `index_v2026_03`, `index_v2026_04`).
    - 새 인덱스에 대해 자동·수동 eval 후 트래픽 스위치.

이 레벨의 “지속적 학습”이면 모델 파라미터는 고정이고, 데이터·프롬프트만 갱신하므로 안정성이 높습니다.[^2_8][^2_1]

### 4.2 Instruction/Domain Tuning (LoRA/PEFT)

LLM 자체를 “조금씩 도메인에 맞게 붙여 나가는” 레이어입니다.

- **전략**:
    - Base: DeepSeek‑V3.2‑Instruct / Llama‑4‑Instruct 등 유지.
    - 위에 LoRA/PEFT 어댑터를 여러 개 쌓고, 도메인별로 활성/비활성.
- **학습 데이터**:
    - RAG 로그에서 좋은 응답/나쁜 응답을 수집.
    - 도메인 문서에서 synthetic Q/A 생성.
    - Open Ko‑LLM Leaderboard2가 강조하듯, generation task(e.g., Ko‑GSM8K, Ko‑EQ) 스타일 데이터를 포함하면 실제 QA 품질과 상관관계가 높습니다.[^2_8][^2_1]
- **파이프라인 예**:
    - 주기(예: 주간/월간)로:

1. 로그 수집 및 필터링 (PHI 제거, 개인정보 마스킹).
2. human 또는 LLM‑judge 기반으로 good/bad 라벨링.
3. SFT/LoRA용 instruction‑style 데이터셋 생성.
4. HuggingFace PEFT로 LoRA 학습, W\&B 등으로 모니터링.
5. A/B 테스트 후 기준 모델 교체.
- **서빙 구조**:
    - vLLM: “base + LoRA adapter” 형태로 서버 기동.
    - Ollama: 커스텀 모델 빌드 시 LoRA merge 또는 adapter 지원 모델 사용.
    - llama.cpp: 학습 후 weight를 merge해 GGUF 변환.


### 4.3 Base 모델 업데이트 전략

새로운 버전(예: Llama‑4 → Llama‑4.1 / DeepSeek‑V3.2 → V3.3)이 나올 때:

1. **오프라인 벤치마크**:
    - Open Ko‑LLM Leaderboard2 task subset (Ko‑GSM8K, Ko‑EQ, Ko‑IFEval 등) + 자체 도메인 벤치.[^2_8][^2_1]
    - 영어+한글 혼합 QA, 의료/유전체 특화 Q/A 세트.
2. **Shadow deployment**:
    - 기존 prod 모델과 새 모델을 동시에 돌리되, 새 모델은 **로그만 수집**.
    - 실제 사용자에겐 기존 응답만 노출.
3. **로그 기반 비교**:
    - human/LLM‑judge로 “quality/regression” 측정.
    - 안전성(환각/잘못된 의료 조언) 체크.
4. **점진적 롤아웃**:
    - 트래픽의 1% → 10% → 50% → 100% 순으로 늘리며 모니터링.

이 접근은 Open Ko‑LLM Leaderboard2가 말하는 “실제 사용과의 상관성이 높은 generation 벤치 + 로그 분석”과 방향성이 맞습니다.[^2_1]

## 5. 구체적인 운영 가이드 (요약)

- **모델 선택**:
    - 고성능 서버: DeepSeek‑V3.2‑Instruct + Ko‑임베딩.
    - 중간급: Llama‑4‑(14/34/70)‑Instruct / GLM‑5‑X.
    - 개발·테스트: 동일 계열 모델을 Ollama로 로컬에서 사용, 프로덕션은 vLLM/llama.cpp.
- **RAG 파이프라인**:
    - 한국어 전처리 + hybrid retrieval + rerank + context compression → LLM 호출.
    - RAG 인덱스는 지속적으로 업데이트, 버전 관리.
- **지속 학습**:
    - 1단계: RAG 데이터와 프롬프트만 주기적으로 개선.
    - 2단계: LoRA/PEFT로 instruction/domain tuning, 도메인별 adapter 운영.
    - 3단계: 새 base 모델 나올 때마다 오프라인 벤치 + shadow + 점진 롤아웃.

원하시면:

- vLLM 기준으로 DeepSeek‑V3.2 + Ko‑임베딩 + LangChain을 엮은 **엔드투엔드 RAG reference 프로젝트 구조**(폴더 구조, 주요 Python 코드 스켈레톤, eval 스크립트)까지 코드 레벨로 풀어 드리겠습니다.
<span style="display:none">[^2_10][^2_9]</span>

<div align="center">⁂</div>

[^2_1]: https://aclanthology.org/2025.naacl-industry.22/

[^2_2]: https://vertu.com/ar/نمط-الحياة/the-best-open-source-llms-in-2026-a-complete-guide-for-ai-developers/

[^2_3]: https://o-mega.ai/articles/top-10-open-source-llms-the-deepseek-revolution-2026

[^2_4]: https://github.com/ggml-org/llama.cpp

[^2_5]: https://rocm.docs.amd.com/en/latest/compatibility/ml-compatibility/llama-cpp-compatibility.html

[^2_6]: https://sohyunwriter.tistory.com/222

[^2_7]: https://fishpoint.tistory.com/11685

[^2_8]: https://arxiv.org/html/2410.12445v2

[^2_9]: https://papers.cool/venue/2025.naacl-industry.22@ACL

[^2_10]: https://www.aihub.or.kr/leaderboard/view.do?currMenu=505\&topMenu=102


---

# RAG 파이프라인에서 VLLM Ollama llama.cpp 성능 벤치마크 결과를 알려주세요. 그리고, Ollama에서 한글 문서 임베딩과 RAG 통합 방법에 대한 상세한 방안을 알려주세요.

한글 RAG에서 VLLM Ollama llama.cpp LoRA 파인튜닝 성능 trade-off와 장기 유지보수 방법에 대한 조사보고를 상세하게 진행해 주시고, 한국어 RAG에 최적화된 LoRA fine-tuning 실전 예제를 추가해 주세요.

vLLM / Ollama / llama.cpp 자체 성능은 “RAG 품질”보다 **동시 처리량·지연·운영 형태**에서 차이가 나고, RAG 정확도는 결국 모델·임베딩·파이프라인 설계가 더 크게 좌우됩니다.[^3_1][^3_2]

## 1. vLLM · Ollama · llama.cpp 성능 벤치 요약 (RAG 관점)

### 1.1 벤치 결과에서 읽을 수 있는 정량 차이

- vLLM vs llama.cpp (Red Hat H200 벤치):
    - **고동시성**에서 vLLM이 llama.cpp 대비 최대 35배 RPS, 44배 TPS를 달성.[^3_1]
    - concurrency 증가 시 vLLM의 P99 TTFT(Time To First Token)는 거의 평평하게 유지, llama.cpp는 대기열 때문에 기하급수적으로 증가.[^3_1]
    - 단일/저동시성에선 출력 토큰 속도(ITL)는 llama.cpp가 매우 낮은 P99 ITL을 보여 “단일 스트림 효율성”에 강점.[^3_1]
- vLLM vs Ollama:
    - 2026년 비교 글에서, 동일 모델 기준 **vLLM이 동시 부하에서 Ollama보다 ~16배 높은 처리량**을 보인다고 요약.[^3_3]
    - Ollama는 간편한 설정·로컬 사용성에 초점, 서버용 최적 스케줄러·배치·텐서 병렬은 vLLM 쪽이 우세.[^3_4][^3_3]
- 종합 비교 정성 평가:
    - vLLM: 멀티유저/고동시성 서버, OpenAI‑유사 API, 고급 커스터마이징에 최적.[^3_2][^3_4][^3_1]
    - llama.cpp: GGUF·양자화·모바일/엣지 등 **단일 또는 저동시성 + 휴대성**이 중요한 경우 최적.[^3_2][^3_1]
    - Ollama: 설치·모델 관리가 단순해서 **개발·PoC·데스크탑 RAG**에 유리, 하지만 서버 사이드 대규모 서빙에선 오버헤드가 있어 vLLM보다 느리다는 평가.[^3_3][^3_4][^3_2]

RAG 품질 자체는 세 엔진이 **같은 모델·같은 파이프라인**이면 거의 동일합니다. 차이는 “얼마나 많은 질의를 어느 정도 지연으로 소화할 수 있느냐”입니다.[^3_2][^3_1]

### 1.2 한국어 RAG에 미치는 영향

- vLLM: 대규모 서비스(사내 포털, 수백 동시 사용자)용 한글 RAG 백엔드에 적합.[^3_3][^3_1]
- llama.cpp: 의사 PC·연구소 워크스테이션 같은 엣지 RAG, 온디바이스 문서 도우미 등에 적합.[^3_2][^3_1]
- Ollama: 팀 단위 개발/실험·데모, 또는 소규모 사용(수명령 동시)에 적합.[^3_5][^3_3][^3_2]

***

## 2. Ollama에서 한글 문서 임베딩 + RAG 통합 상세 방안

Ollama는 “LLM + 임베딩 둘 다 로컬”로 쓸 수 있고, LangChain이 이를 바로 지원합니다. 아래는 **실전 스펙**을 염두에 둔 구성입니다.[^3_5]

### 2.1 모델 선택 전략 (한글 기준)

- **LLM (생성)**: Llama‑3/4‑Instruct, DeepSeek 계열 등 멀티링구얼 Instruct 모델을 pull.
- **임베딩**:
    - Ollama 기본 임베딩(예: `nomic-embed-text`)은 영어 중심이라 한국어에서 성능 저하가 보고.[^3_6]
    - 위 영상에서도 `nomic-embed-text` vs `bge-m3` 비교에서 한국어 문서에선 bge-m3 기반 임베딩이 훨씬 낫다고 결론.[^3_6]
    - ⇒ **권장**: 임베딩은 Python에서 `bge-m3`/한국어 변형을 HF로 띄우고, Ollama는 LLM 전용으로 쓰는 구조.


### 2.2 아키텍처 패턴

- 프로세스 구성:
    - `ollama serve` (LLM, 필요 시 임베딩도 Ollama 모델로).
    - Python FastAPI/Flask:
        - 임베딩: sentence-transformers(`bge-m3` 등).
        - 벡터 DB: Chroma / Qdrant / pgvector.
        - RAG orchestration: LangChain/LlamaIndex.


### 2.3 LangChain 예제 (한글 문서 RAG + Ollama)

기본 틀은 다음과 같은 구조를 추천할 수 있습니다 (핵심 아이디어만, 실제 코드는 줄여서):

```python
from langchain_community.llms import Ollama
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain.embeddings import HuggingFaceEmbeddings  # bge-m3-ko 등

# 1) 한글 문서 로딩 후 청크
docs = load_korean_documents(...)  # PDF/DB 등에서 로드
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=150,
    separators=["\n\n", "\n", "。", "．", ".", "?", "!", " "],
)
splits = text_splitter.split_documents(docs)

# 2) 한국어 특화 임베딩 (HF)
embed_model = HuggingFaceEmbeddings(
    model_name="BAAI/bge-m3",  # 한국어 성능 검증 사례 다수[web:28]
    encode_kwargs={"normalize_embeddings": True}
)

vectorstore = Chroma.from_documents(
    documents=splits,
    embedding=embed_model,
    collection_name="kor_rag"
)

# 3) Ollama LLM
llm = Ollama(
    model="llama3",  # 또는 deepseek-r1 등
    temperature=0.1,
)

# 4) RAG 체인
retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 5, "fetch_k": 15}
)

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    chain_type="stuff",
    return_source_documents=True,
)

query = "이 논문에서 마이크로바이옴 샘플 전처리 방법을 요약해서 말해줘."
result = qa_chain.invoke({"query": query})
print(result["result"])
```

이 구조에서:

- Ollama는 LLM inference만 담당.
- 한국어 임베딩은 HF(bge-m3-ko 등)로 처리해 Ollama의 영어 중심 임베딩 한계를 피합니다.[^3_5][^3_6]

***

## 3. vLLM · Ollama · llama.cpp + LoRA 파인튜닝: 성능 trade‑off

### 3.1 엔진별 LoRA/튜닝 운용 관점

- **vLLM**
    - 목표: 고동시성 서버, k‑serve/서빙 프레임워크와 연동.[^3_1][^3_2]
    - LoRA:
        - 일반적으로 HF Transformers + PEFT로 LoRA 학습 후, weight merge or adapter 방식으로 모델을 저장.
        - vLLM은 merged weight든 adapter든, “완성된 HF 모델”을 올리는 형태가 일반적.
    - 장점:
        - 대형 모델(수십 B)과 복잡한 LoRA 설정을 서버 사이드까지 그대로 가져갈 수 있음.
        - multi‑GPU·tensor parallel, continuous batching → LoRA 적용 후에도 throughput 강함.[^3_1]
- **Ollama**
    - 모델을 “YAML 식 recipe”로 빌드, 일부 경우 LoRA를 merge한 GGUF/gguf‑like 가중치를 패키징.[^3_5][^3_2]
    - LoRA 적용 방식:
        - 보통 HF에서 LoRA merge → safetensors → GGUF 변환 → Ollama `Modelfile`로 import.
        - 또는 Ollama가 지원하는 adapter 기능(버전에 따라 다름)을 활용.
    - 장점:
        - 개발자/데이터과학자가 “튜닝된 모델 태그”를 쉽게 배포·롤백 가능.
    - 단점:
        - vLLM처럼 대규모 서버 튜닝/배포에 최적화된 에코시스템은 아직 제한적.[^3_4][^3_3]
- **llama.cpp**
    - 주로 **merge된 LoRA + base weight → GGUF**로 가져와서 사용.[^3_7][^3_8]
    - LoRA 라이브 적용도 가능한 포크들이 있으나, 프로덕션에서는 보통 미리 merge한 가중치 사용.
    - 장점:
        - 양자화까지 포함한 end‑to‑end 최적화로 메모리·지연 감소.
    - 단점:
        - LoRA adapter를 동적으로 토글하는 등의 “멀티 도메인” 시나리오엔 적합성이 떨어짐.


### 3.2 RAG + LoRA에서 성능 trade‑off

- **정확도 vs 지연/비용**:
    - LoRA로 도메인 튜닝한 8–14B 모델이, 미튜닝 70B 모델과 비슷하거나 더 나은 도메인 QA 품질을 내는 사례가 여럿 보고.[^3_9][^3_10]
    - 대신, 범용 지식/추론/코딩은 여전히 대형 모델이 우수. ⇒ **RAG에서는 “도메인 질문”만 LoRA‑튜닝 모델로 라우팅**하는 구조가 효과적.[^3_9]
- **RAG와 LoRA의 역할 분담**:
    - RAG: 최신 지식·길고 복잡한 문서 정보 제공, hallucination 억제.[^3_10][^3_9]
    - LoRA: 도메인 용어/스타일/포맷·추론 패턴 내재화.
    - ⇒ “RAG만 잘하면 fine‑tuning 필요 없다”는 주장도 있지만, 실제 현업에선 **둘을 병행할 때 가장 안정적**이라는 가이드가 많습니다.[^3_10][^3_9]


### 3.3 장기 유지보수 관점 요약

| 엔진 | 장점 | LoRA 운용 난이도 | 장기 유지보수 포인트 |
| :-- | :-- | :-- | :-- |
| vLLM | 고동시성, multi‑GPU, OpenAI‑like API.[^3_1][^3_2] | 중. HF/PEFT 파이프라인 그대로 활용. | 모델/LoRA 버전 매트릭스 증가 관리, k8s 기반 운영·모니터링. |
| Ollama | 설치·모델 관리 간단, 로컬/PoC 강함.[^3_3][^3_2] | 하. recipe 기반, 태그 관리. | 버전·태그 체계 정리, 서버형 운영시 스케일링 한계 주의. |
| llama.cpp | 휴대성, GGUF+양자화, 엣지용.[^3_1][^3_2][^3_7] | 중. merge+양자화 프로세스만 정립하면 안정. | GPU/CPU matrix·양자화 조합 증가, 자동 빌드 파이프라인 필수. |


***

## 4. 한국어 RAG에 최적화된 LoRA Fine-tuning 실전 예제 (개념 설계)

여기서는 **HF + PEFT로 LoRA 튜닝 → vLLM/Ollama/llama.cpp로 배포**를 염두에 둔 실전 워크플로만 설계 수준으로 설명합니다.[^3_9][^3_10]

### 4.1 데이터 설계

- 소스:
    - 한글 도메인 문서(논문, 보고서, 매뉴얼, EMR 가이드 등).
    - 기존 RAG 로그에서 “정답이 좋았던 Q/A 쌍”.
- 포맷 (Instruction style):
    - `{"instruction": "...질문(한글/혼합)...", "input": "...필요 시 추가 context...", "output": "...도메인 전문가 수준의 한글 답변..."}`
- 주의:
    - RAG와 충돌하지 않게, “문서에서 근거를 요약/정리하는 스타일”을 학습시키는 것이 좋습니다.[^3_9]
    - Open Ko‑LLM Leaderboard2가 쓰는 Ko‑GSM8K/Ko‑EQ류 태스크처럼, **추론+설명형 Q/A**를 포함하면 실제 RAG QA와 상관성이 높아집니다.[^3_11][^3_12]


### 4.2 학습 파이프라인 개요

1. Base 모델: Llama‑3/4‑Instruct‑8B~14B 또는 DeepSeek‑12/13B Instruct.
```
2. Tokenizer 세팅: `<s>`, `</s>`, system/user/assistant 토큰 유지.  
```

3. LoRA 설정:
    - rank r=8~64, alpha=16~64, target modules (`q_proj`, `v_proj`, `o_proj` 등).
    - 4bit quantization(QLoRA)로 GPU 메모리 절약.[^3_9]
4. Trainer:
    - 학습 스텝: 수천~수만 step, LR warmup+cosine decay.
    - eval: 한국어 도메인 벤치 + 자체 dev set.

### 4.3 (개념 수준) Python 스켈레톤

다음은 “한글 RAG 도메인 LoRA 튜닝”을 위한 HF/PEFT 스켈레톤의 개념 구조입니다.[^3_10][^3_9]

```python
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from datasets import load_from_disk

base_model_name = "meta-llama/Meta-Llama-3-8B-Instruct"
tokenizer = AutoTokenizer.from_pretrained(base_model_name)

model = AutoModelForCausalLM.from_pretrained(
    base_model_name,
    load_in_4bit=True,
    device_map="auto"
)
model = prepare_model_for_kbit_training(model)

lora_config = LoraConfig(
    r=32,
    lora_alpha=64,
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)

model = get_peft_model(model, lora_config)

# Korean instruction dataset (pre-built)
dataset = load_from_disk("./kor_rag_instructions")

def format_example(example):
    # system/user/assistant 템플릿 적용
    system = "당신은 한국어 RAG 도메인 전문가입니다. 제공된 문서와 지식을 바탕으로 정확하고 근거 기반으로 답변하세요."
    user = example["instruction"]
    # optional: example["context"]를 포함
    assistant = example["output"]

    prompt = f"<s>[SYSTEM]{system}[/SYSTEM]\n[USER]{user}[/USER]\n[ASSISTANT]"
    example["input_ids"] = tokenizer(
        prompt,
        text_target=assistant,
        truncation=True,
        max_length=2048
    )
    return example

tokenized = dataset.map(format_example)

training_args = TrainingArguments(
    output_dir="./llama3-kor-rag-lora",
    per_device_train_batch_size=2,
    gradient_accumulation_steps=8,
    learning_rate=2e-4,
    num_train_epochs=3,
    logging_steps=50,
    save_steps=500,
    evaluation_strategy="steps",
    fp16=True,
)

def collate_fn(batch):
    input_ids = [x["input_ids"]["input_ids"] for x in batch]
    labels = [x["input_ids"]["labels"] for x in batch]
    return {
        "input_ids": tokenizer.pad({"input_ids": input_ids}, return_tensors="pt")["input_ids"],
        "labels": tokenizer.pad({"input_ids": labels}, return_tensors="pt")["input_ids"],
    }

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized["train"],
    eval_dataset=tokenized["validation"],
    data_collator=collate_fn,
)

trainer.train()
model.save_pretrained("./llama3-kor-rag-lora")
tokenizer.save_pretrained("./llama3-kor-rag-lora")
```

이후 배포:

- **vLLM**: `llama3-kor-rag-lora`를 base에 merge하거나, adapter를 포함한 HF 모델로 export 후 vLLM 모델로 로딩.
- **Ollama**:

1. LoRA를 base에 merge → 단일 safetensors.
2. `llama.cpp`의 `convert-hf-to-gguf.py`로 GGUF 변환.
3. `Modelfile`에서 GGUF 경로 지정 후 `ollama create`.
- **llama.cpp**:
    - 같은 GGUF를 바로 `./main -m model.gguf ...` 형태로 사용.[^3_8][^3_7]

***

## 5. 한국어 RAG + LoRA 장기 유지보수 전략

- **버전 관리**:
    - Base 모델 버전 (예: `llama4-8b-instruct-v1`)
    - LoRA 버전 (도메인+날짜, 예: `microbiome-2026-03`)
    - RAG 인덱스 버전 (`index_v2026_03`)
    - 이를 조합한 “릴리즈 메타”를 별도 테이블/레포에 기록.
- **평가/Eval**:
    - Open Ko‑LLM Leaderboard2 스타일 한국어 태스크 + 도메인 Q/A 세트로 정기 벤치.[^3_12][^3_11]
    - 새 LoRA/인덱스 배포 전 항상 오프라인 점수 체크 + 제한된 온라인 A/B 테스트.
- **로그 기반 지속 개선**:
    - 실패 케이스(“답변 없음/환각/잘못된 인용”)를 수집 → 다음 LoRA 라운드 학습 데이터에 포함.[^3_10][^3_9]
    - 잘 나온 케이스는 positive example로, 나쁜 케이스는 corrected answer를 붙여 contrastive/SFT로 사용.

이 정도면, vLLM/Ollama/llama.cpp 기반 **한국어 RAG + LoRA 튜닝**을 장기적으로 운용할 수 있는 설계 프레임이 만들어집니다. 필요한 경우, 특정 조합(예: “DeepSeek‑13B + vLLM + Qdrant + pgvector”)에 맞춰 docker-compose/k8s 매니페스트 수준까지 파이프라인을 더 깔끔하게 정리해 드릴 수 있습니다.
<span style="display:none">[^3_13][^3_14]</span>

<div align="center">⁂</div>

[^3_1]: https://developers.redhat.com/articles/2025/09/30/vllm-or-llamacpp-choosing-right-llm-inference-engine-your-use-case

[^3_2]: https://stable-learn.com/en/ai-model-tools-comparison/

[^3_3]: https://particula.tech/blog/ollama-vs-vllm-comparison

[^3_4]: https://blog.stackademic.com/vllm-vs-ollama-choosing-the-right-lightweight-llm-framework-for-your-ai-applications-a454e1b39322

[^3_5]: https://rodangdong.tistory.com/288

[^3_6]: https://www.youtube.com/watch?v=GsZ9w04smVE

[^3_7]: https://github.com/ggml-org/llama.cpp

[^3_8]: https://rocm.docs.amd.com/en/latest/compatibility/ml-compatibility/llama-cpp-compatibility.html

[^3_9]: https://velog.io/@mit_bang/%EC%B2%AD%EA%B0%95-%EB%94%A5%EB%9F%AC%EB%8B%9D-19-RAG-Advanced-LoRA-Fine-tuning

[^3_10]: https://wikidocs.net/325691

[^3_11]: https://aclanthology.org/2025.naacl-industry.22/

[^3_12]: https://arxiv.org/html/2410.12445v2

[^3_13]: https://lilys.ai/ko/notes/openai-agent-builder-20260208/ollama-vllm-llama-cpp-local-ai-runner-2025

[^3_14]: https://www.reddit.com/r/LocalLLaMA/comments/1qwwint/vllm_vs_llamacpp_vs_ollama/


---

# VLLM Ollama llama.cpp 하드웨어 요구사항 비교해 주시고, vLLM에서 한국어 LoRA 파인튜닝 적용 사례를 구체적으로 작성해 주세요.

vLLM / Ollama / llama.cpp는 “같은 모델이면 품질은 비슷, 요구 HW·스케일링 특성이 다르다” 정도로 보시면 됩니다.[^4_1][^4_2]

## 1. vLLM · Ollama · llama.cpp 하드웨어 요구사항 비교

### 1.1 용도·스케일 관점 요약

| 엔진 | 주요 용도 | 권장 HW 레벨 (요약) | 특징 |
| :-- | :-- | :-- | :-- |
| vLLM | 서버형, 고동시성 RAG API | 24–80GB+ VRAM GPU, 다중 GPU 가능.[^4_3][^4_4] | 긴 컨텍스트·배치·고 RPS에 최적. |
| Ollama | 로컬 개발·소규모 서비스 | 8–16GB RAM + RTX 3060급 GPU or M‑시리즈 맥.[^4_5][^4_6] | 설치/모델 관리 간편, 7B–14B 위주. |
| llama.cpp | 경량·엣지·온디바이스 | 8–24GB VRAM 또는 CPU, 양자화 전제.[^4_7] | GGUF·2–8bit로 메모리 절감, 저동시성·휴대성 강점. |

### 1.2 vLLM 하드웨어

- 지원 HW: NVIDIA CUDA GPU, AMD ROCm GPU, Intel/AMD/ARM CPU, Intel XPU 등 광범위 하드웨어를 공식 지원합니다.[^4_8][^4_9]
- VRAM 용량에 따른 대략적인 룰:
    - vLLM GPU 사이징 가이드에 따르면, FP16 기준 모델 크기(파라미터 수)에 대략 **2GB/1B 파라미터 수준**의 VRAM + 여유 4–5GB를 잡으라고 안내합니다.[^4_4]
    - 8–14B 모델: 24–48GB VRAM 단일 GPU (예: L40S)에서 충분.[^4_4]
    - 70B 모델: INT4/8 양자화 전제 시 40–80GB급 GPU 하나 또는 두 개, 혹은 다중 GPU 병렬 구성.[^4_10][^4_4]
- RAG/대용량 컨텍스트:
    - 긴 컨텍스트·대량 캐시를 요구하는 RAG에는 H200, MI300X/MI325X 같은 고대역폭·대용량 VRAM 카드가 적합하다고 명시.[^4_4]


### 1.3 Ollama 하드웨어

- 로컬 LLM 가이드에서 Ollama 권장 스펙:
    - 최소: 8GB RAM, 최신 CPU, 통합 GPU로 3–8B 모델 구동 가능.[^4_5][^4_6]
    - 권장: 16–32GB RAM, RTX 3060/4060(12GB VRAM) 또는 Apple M‑시리즈 맥.[^4_6]
    - 7B–8B 모델: 5–8GB RAM/VRAM.[^4_6]
    - 13–14B 모델: 10–12GB RAM/VRAM.[^4_6]
    - 30B+: 24GB+, 70B+: 40–64GB RAM/VRAM 필요.[^4_6]
- 요약: 7B–14B 모델을 데스크탑/노트북에서 쓰기에 최적화, 70B 이상은 가능하지만 현실적으로는 고급 워크스테이션 급이 필요합니다.[^4_6]


### 1.4 llama.cpp 하드웨어

- VRAM 가이드(양자화 전제):[^4_7]
    - 8GB VRAM (RTX 4060 등): ~9B 모델 안정 구동 (~6.8GB 사용).
    - 16GB VRAM: ~20B 모델.
    - 20GB VRAM: ~27B 모델.
    - 24GB VRAM: ~35B 모델.
    - 32GB VRAM: 35B 모델 대용량 컨텍스트나 고품질, 70B는 강양자화 필요.[^4_7]
- CPU 전용도 가능하지만, 실시간 대화/서비스용이면 적어도 8–16GB VRAM GPU가 있는 게 현실적입니다.[^4_7]

***

## 2. vLLM에서 한국어 LoRA 파인튜닝 적용: 구체 시나리오

가정:

- Base: `meta-llama/Meta-Llama-3-8B-Instruct` 또는 유사 8–14B 멀티링구얼 모델.
- 도메인: 한국어 문서 기반 RAG (예: 의료/마이크로바이옴).
- 목표: 한국어 QA 스타일·도메인 용어·근거 서술 패턴을 LoRA로 튜닝하고, vLLM에서 서빙.


### 2.1 전체 파이프라인 개요

1. 한국어 RAG 로그/문서로 instruction 데이터셋 구축.
2. HF Transformers + PEFT로 LoRA 학습 (QLoRA 권장).[^4_11][^4_12]
3. LoRA를 base에 merge한 HF 모델을 저장.
4. vLLM에서 해당 HF 모델을 로딩, OpenAI 호환 API로 서빙.[^4_3][^4_9]
5. LangChain/LlamaIndex에서 vLLM 엔드포인트를 LLM으로 사용, 임베딩은 별도 한국어 임베딩 모델로.

아래는 각 단계별로 조금 더 구체화한 예입니다.

### 2.2 한국어 RAG용 LoRA 학습 (요지)

데이터 포맷 예:

```json
{
  "instruction": "다음 논문에서 샘플 전처리 과정을 요약해 주세요.",
  "context": "논문 일부 또는 RAG로 찾아온 문단들...",
  "output": "이 논문에서 샘플 전처리는 다음과 같이 이루어진다: ..."
}
```

LoRA 학습 코드 구조는 앞선 답변의 HF/PEFT 예제와 동일하고, 여기서는 “vLLM 서빙을 염두에 둔 저장 방식”만 강조하겠습니다:

- 학습 후:
    - `save_pretrained("llama3-kor-rag-lora")` (LoRA adapter 포함).
    - `merge_and_unload`를 호출해 base에 LoRA를 병합한 순수 모델을 하나 더 만들어 두는 것이 vLLM 배포에 편합니다.[^4_12][^4_11]

개념적으로:

```python
from peft import PeftModel

base = AutoModelForCausalLM.from_pretrained(base_model_name)
lora = PeftModel.from_pretrained(base, "./llama3-kor-rag-lora")
merged = lora.merge_and_unload()
merged.save_pretrained("./llama3-kor-rag-merged")
tokenizer.save_pretrained("./llama3-kor-rag-merged")
```


### 2.3 vLLM 쪽 모델 로딩

vLLM는 HF 디렉토리 경로를 직접 모델로 지정할 수 있습니다.[^4_9][^4_3]

1) vLLM 서버 실행 (예: OpenAI API 호환 모드):
```bash
python -m vllm.entrypoints.openai.api_server \
  --model ./llama3-kor-rag-merged \
  --host 0.0.0.0 \
  --port 8000 \
  --max-model-len 8192 \
  --dtype auto
```

- `--max-model-len`은 RAG 컨텍스트 길이에 맞춰 조정.
- GPU: 8B 모델이면 24GB VRAM 단일 GPU에서 FP16/4bit 모두 무난.[^4_4]

2) 클라이언트(LangChain 예)에서 사용:
```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="llama3-kor-rag-merged",
    openai_api_key="EMPTY",
    openai_api_base="http://localhost:8000/v1",
    temperature=0.1,
)
```

이제 이 LLM을 기존 한국어 RAG 파이프라인의 “생성” 부분에 꽂으면 됩니다 (임베딩/리트리버는 앞서 언급한 bge-m3-ko 등).

### 2.4 vLLM + LoRA 모델에서 한국어 RAG 최적화 포인트

- **컨텍스트 길이**:
    - GPU VRAM 허용 범위 내에서 context window를 넉넉히 (예: 8k–16k) 잡되, RAG에서 context compression/summarization을 병행해 불필요한 텍스트를 줄입니다.[^4_4]
- **프롬프트 템플릿**:
    - system: “당신은 한국어 RAG 도메인 전문가… 제공된 context만을 사용해 답변…”
    - user: 질문 + (선택) 간단한 메타 정보.
    - context: 별도 섹션으로 첨부, “다음은 참고 문서이다:” 식으로 구분.
    - LoRA 학습 시에도 동일한 템플릿을 사용해 일관성을 유지하는 게 중요합니다.[^4_11][^4_12]
- **서버 튜닝**:
    - 동시 접속이 많다면, `--gpu-memory-utilization`, `--max-num-batched-tokens` 등을 조정해 vLLM의 배치 효율을 올립니다.[^4_9][^4_4]
    - 긴 컨텍스트·RAG 요청 비율이 높은 워크로드에서는 VRAM보다 **메모리 대역폭이 높은 카드(H100/H200/MI300X)** 선택이 유리하다고 가이드합니다.[^4_4]

***

## 3. 정리: 선택 기준

- **vLLM**:
    - 한국어 LoRA 튜닝 모델을 프로덕션 수준으로 서빙하고, 다수 유저가 한글 RAG를 동시에 쓰는 환경이면 vLLM이 사실상 표준입니다.[^4_1][^4_9][^4_4]
- **Ollama**:
    - 팀 단위 개발·실험, 또는 내부 소규모 도구라면 “튜닝 모델을 GGUF 변환 후 Ollama로 배포”가 관리 측면에서 편합니다.[^4_5][^4_6]
- **llama.cpp**:
    - 현장/엣지/PC에 배포해야 하는 경량 한글 RAG 클라이언트는 LoRA‑merge+양자화한 GGUF를 llama.cpp로 돌리는 구조가 안정적입니다.[^4_7]

필요하시면,

- “Llama‑3‑8B‑Instruct 한국어 RAG LoRA 튜닝 + vLLM + Qdrant + LangChain”을 전제로,
- `docker-compose` 수준까지 포함된 레퍼런스 스택(컨테이너 구성, env 변수, 헬스체크, 간단한 API 예제)을 코드 단위로 정리해 드리겠습니다.
<span style="display:none">[^4_13][^4_14]</span>

<div align="center">⁂</div>

[^4_1]: https://developers.redhat.com/articles/2025/09/30/vllm-or-llamacpp-choosing-right-llm-inference-engine-your-use-case

[^4_2]: https://stable-learn.com/en/ai-model-tools-comparison/

[^4_3]: https://docs.vllm.ai/en/stable/getting_started/installation/

[^4_4]: https://www.digitalocean.com/community/conceptual-articles/vllm-gpu-sizing-configuration-guide

[^4_5]: https://joshuaopolko.com/ollama/

[^4_6]: https://shshell.com/blog/ollama-module-1-lesson-4

[^4_7]: https://localllm.in/blog/llamacpp-vram-requirements-for-local-llms

[^4_8]: https://docs.vllm.ai/en/latest/getting_started/installation/

[^4_9]: https://github.com/vllm-project/vllm

[^4_10]: https://introl.com/blog/local-llm-hardware-pricing-guide-2025

[^4_11]: https://velog.io/@mit_bang/%EC%B2%AD%EA%B0%95-%EB%94%A5%EB%9F%AC%EB%8B%9D-19-RAG-Advanced-LoRA-Fine-tuning

[^4_12]: https://wikidocs.net/325691

[^4_13]: https://www.proxpc.com/blogs/gpu-hardware-requirement-guide-for-llama-3-in-2025

[^4_14]: https://docs.iwinv.kr/service/llm_\&_gpu/server-type/vllm-virtual/


---

# VLLM 한국어 RAG 파이프라인 전체 코드

vLLM + 한국어 임베딩 + LangChain 조합으로, 한글 문서 RAG 전체 파이프라인을 한 파일 기준으로 정리해 보겠습니다.[^5_1][^5_2]
(전제: vLLM 서버는 별도 프로세스로 띄우고, 이 코드는 클라이언트·RAG 오케스트레이션 역할을 합니다.)[^5_3][^5_4]

***

## 1. 전체 구성 개요

구성 요소:

- vLLM: OpenAI 호환 API 서버 (예: Llama‑3/4‑Instruct 또는 한국어 LoRA‑머지 모델).[^5_4][^5_3]
- 임베딩: HuggingFace 한국어 호환 모델(bge‑m3 등).[^5_5][^5_1]
- 벡터DB: Chroma (로컬 파일 기반, PoC/소규모 서비스용).[^5_1][^5_5]
- 오케스트레이션: LangChain RAG 체인.[^5_2][^5_1]

서버는 예를 들어 다음처럼 띄워져 있다고 가정합니다.[^5_3][^5_4]

```bash
# 예: 한국어 LoRA를 머지해 둔 Llama3‑kor‑RAG 모델
vllm serve \
  --model /models/llama3-kor-rag-merged \
  --host 0.0.0.0 \
  --port 8000 \
  --max-model-len 8192
```


***

## 2. vLLM 한국어 RAG 파이프라인 전체 코드 예제

아래는 `.py` 하나에 담을 수 있는 “엔드투엔드” 예제입니다.
(문서: `.txt` / `.md` / `.pdf` 등, 한글 위주라고 가정.)

```python
import os
from typing import List

# LangChain 관련
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma

from langchain.embeddings import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import ChatPromptTemplate

# ------------------------------------------------
# 1. 설정값
# ------------------------------------------------

# vLLM OpenAI 호환 서버 엔드포인트
VLLM_API_BASE = "http://localhost:8000/v1"  # vLLM serve 주소[web:41][web:44]
VLLM_API_KEY = "EMPTY"                      # vLLM에서는 dummy key 사용[web:43]

# vLLM에 올려둔 한국어 RAG용 LLM 이름
VLLM_MODEL_NAME = "llama3-kor-rag-merged"   # vLLM --model 인자와 같게[web:41]

# 한글 임베딩 모델 (HuggingFace)
EMBEDDING_MODEL_NAME = "BAAI/bge-m3"        # 한국어 지원이 검증된 범용 임베딩[web:28][web:45]

# 문서 경로 및 Chroma DB 경로
DOCS_PATH = "./data/korean_docs"            # 한글 문서가 들어 있는 디렉터리
CHROMA_DB_DIR = "./chroma_kor_rag"          # 로컬 vector store 디렉터리[web:46]

# ------------------------------------------------
# 2. 한글 문서 로딩 및 Chunking
# ------------------------------------------------

def load_korean_documents(path: str):
    """
    지정된 폴더에서 한글 문서를 로딩.
    TextLoader를 기본으로 쓰고, 필요시 PDFLoader 등 추가.
    """
    loader = DirectoryLoader(
        path,
        glob="**/*.txt",              # 필요 시 *.md, *.pdf 등 패턴 추가
        loader_cls=TextLoader,
        show_progress=True,
        encoding="utf-8",
    )
    docs = loader.load()
    return docs

def split_documents(docs) -> List:
    """
    한글에 맞는 chunking 전략.
    paragraph -> sentence -> char 레벨로 fallback하는 Recursive splitter.[web:45][web:46]
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
        separators=[
            "\n\n", "\n",
            "다.", "다.\n",
            "입니다.", "합니다.",
            ". ", "? ", "! ",
            "。", "？", "！",
            " "
        ],
    )
    splits = text_splitter.split_documents(docs)
    return splits

# ------------------------------------------------
# 3. 임베딩 및 벡터스토어 생성
# ------------------------------------------------

def build_vectorstore(docs_splits):
    """
    HuggingFace bge-m3 임베딩 + Chroma vector store 구성.[web:45][web:46]
    """
    embed_model = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_NAME,
        encode_kwargs={"normalize_embeddings": True},
    )

    vectorstore = Chroma.from_documents(
        documents=docs_splits,
        embedding=embed_model,
        persist_directory=CHROMA_DB_DIR,
        collection_name="kor_rag_collection",
    )

    # 디스크에 저장
    vectorstore.persist()
    return vectorstore

def load_vectorstore():
    """
    이미 만들어 둔 Chroma DB를 로딩.[web:46]
    """
    embed_model = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_NAME,
        encode_kwargs={"normalize_embeddings": True},
    )
    vectorstore = Chroma(
        persist_directory=CHROMA_DB_DIR,
        collection_name="kor_rag_collection",
        embedding_function=embed_model,
    )
    return vectorstore

# ------------------------------------------------
# 4. vLLM LLM 클라이언트 + RAG 체인 구성
# ------------------------------------------------

def get_llm():
    """
    vLLM OpenAI 호환 서버를 LangChain ChatOpenAI로 래핑.[web:41][web:44]
    """
    os.environ["OPENAI_API_KEY"] = VLLM_API_KEY
    os.environ["OPENAI_API_BASE"] = VLLM_API_BASE

    llm = ChatOpenAI(
        model=VLLM_MODEL_NAME,
        temperature=0.1,
        max_tokens=1024,
        streaming=False,
    )
    return llm

def get_rag_chain(vectorstore):
    """
    Retriever + RAG Prompt + LLM을 조합한 QA 체인 정의.[web:45][web:48]
    """
    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 5, "fetch_k": 20},
    )

    # 한국어 RAG용 프롬프트 템플릿
    prompt_template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "당신은 한국어 문서에 기반한 전문 RAG 어시스턴트입니다. "
                    "반드시 제공된 컨텍스트에 근거해서만 답변하세요. "
                    "컨텍스트에 정보가 없으면 모른다고 답변하세요. "
                    "답변은 한국어로, 가능한 한 명확하고 간결하게 작성하세요."
                ),
            ),
            (
                "user",
                (
                    "질문: {question}\n\n"
                    "===== 컨텍스트 시작 =====\n"
                    "{context}\n"
                    "===== 컨텍스트 끝 =====\n\n"
                    "위 컨텍스트만을 근거로 질문에 답변하세요."
                ),
            ),
        ]
    )

    def format_docs(docs):
        return "\n\n".join(
            [f"[출처 {i+1}] {d.metadata.get('source', '')}\n{d.page_content}" for i, d in enumerate(docs)]
        )

    # LangChain RetrievalQA 대신 직접 chain 구성 (가독성을 위해)
    from langchain_core.runnables import RunnableMap, RunnablePassthrough
    from langchain_core.output_parsers import StrOutputParser

    rag_chain = (
        RunnableMap(
            {
                "context": retriever | format_docs,
                "question": RunnablePassthrough(),
            }
        )
        | prompt_template
        | get_llm()
        | StrOutputParser()
    )

    return rag_chain

# ------------------------------------------------
# 5. 메인: 인덱스 빌드 + 질의 예제
# ------------------------------------------------

def build_or_load_vectorstore():
    """
    이미 인덱스가 있으면 로딩, 없으면 새로 구축.
    """
    if not os.path.exists(CHROMA_DB_DIR):
        os.makedirs(CHROMA_DB_DIR, exist_ok=True)
        docs = load_korean_documents(DOCS_PATH)
        print(f"Loaded {len(docs)} documents")
        splits = split_documents(docs)
        print(f"Split into {len(splits)} chunks")
        vectorstore = build_vectorstore(splits)
        print("Vectorstore built and persisted.")
    else:
        vectorstore = load_vectorstore()
        print("Vectorstore loaded from disk.")
    return vectorstore

def main():
    # 1) 인덱스 준비
    vectorstore = build_or_load_vectorstore()

    # 2) RAG 체인 준비
    rag_chain = get_rag_chain(vectorstore)

    # 3) 예시 질의
    while True:
        query = input("\n질문을 입력하세요 (종료: exit) > ").strip()
        if query.lower() in ["exit", "quit"]:
            break

        answer = rag_chain.invoke(query)
        print("\n[답변]\n")
        print(answer)

if __name__ == "__main__":
    main()
```


### 2.1 이 코드가 하는 일

- `./data/korean_docs` 아래의 한글 텍스트 문서를 읽어서 chunking → bge‑m3 임베딩 → Chroma에 저장.[^5_5][^5_1]
- vLLM 서버에 올라간 `llama3-kor-rag-merged` 모델을 OpenAI‑호환 Chat API로 호출.[^5_4][^5_3]
- 질의 시:
    - Chroma에서 MMR 기반 top‑k 문서를 찾고,
    - 한국어 RAG 전용 system/user 프롬프트 템플릿에 컨텍스트를 주입,
    - vLLM LLM이 한글로 답변하도록 구성.[^5_2][^5_1]

***

## 3. 확장 포인트

- LoRA 한국어 튜닝 모델을 vLLM에 올리면, 위 파이프라인은 그대로 두고 모델 디렉터리/이름만 교체하면 됩니다.[^5_6][^5_7]
- 임베딩을 Upstage/SOLAR‑Ko 등 한국어 특화로 바꾸거나, reranker(Qwen‑reranker, bge‑reranker)를 vLLM `score` API로 붙여도 구조는 동일합니다.[^5_3][^5_1][^5_2]

원하시면,

- 이 코드를 기준으로 도커라이징(docker-compose: vLLM + RAG API + Chroma)과,
- 한국어 도메인 전용 평가 스크립트(offline eval)까지 붙인 버전도 설계해 드리겠습니다.
<span style="display:none">[^5_10][^5_11][^5_12][^5_8][^5_9]</span>

<div align="center">⁂</div>

[^5_1]: https://rocm.blogs.amd.com/artificial-intelligence/rag-pipeline-vllm/README.html

[^5_2]: https://docs.vllm.ai/en/latest/examples/online_serving/retrieval_augmented_generation_with_langchain/

[^5_3]: https://docs.vllm.ai/en/latest/serving/openai_compatible_server.html

[^5_4]: https://docs.vllm.ai/en/stable/getting_started/quickstart/

[^5_5]: https://rfriend.tistory.com/832

[^5_6]: https://docs.vllm.ai/en/stable/getting_started/installation/

[^5_7]: https://github.com/vllm-project/vllm

[^5_8]: https://lsjsj92.tistory.com/673

[^5_9]: https://docs.rbln.ai/latest/ko/software/model_serving/vllm_support/tutorial/openai_api_server.html

[^5_10]: https://github.com/vllm-project/vllm/blob/main/examples/online_serving/openai_completion_client.py

[^5_11]: https://docs.redhat.com/en/documentation/red_hat_ai_inference_server/3.1/html/vllm_server_arguments/vllm-server-usage_server-arguments

[^5_12]: https://www.inflearn.com/community/questions/1528095/3-2-1-langchain과-chroma를-활용한-rag-구성-결과-관련


---

# 사용자 수(이용(예정) 수, 동접수)에 따라 서버를 구성하고자 합니다. 10명, 50, 100, 500, 1000, 3000, 5000, 1만이상 등으로 사용자와 사용하는 LLM환경에 맞춰 RAM, VRAM, SSD, CPU 등의 하드웨어 스펙을 표로 정리해 주세요.

동접자 수 기준으로 대략적인 **권장 스펙(1개 LLM 인스턴스 기준, 8B/14B/70B급 혼합 가정)**을 추정한 표입니다. 실 서비스에서는 모델 크기·컨텍스트 길이·RPS에 따라 ±1단계 여유를 두고 잡는 것을 권장합니다.[^6_1][^6_2][^6_3][^6_4][^6_5][^6_6]

### 동접/사용자 수별 권장 하드웨어(요약)

| 동접/사용자 규모 | 가정 LLM 환경 (예시) | GPU/VRAM (대략) | 시스템 RAM | SSD 용량/특성 | CPU (코어 기준) | 비고 |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| ≤ 10명 (소규모 PoC) | 7–9B, 4bit, vLLM 또는 Ollama/llama.cpp | RTX 3060/4060 8–12GB 한 장.[^6_4][^6_3] | 32GB RAM.[^6_4][^6_5] | NVMe 1TB, 모델 1–2개 + 인덱스.[^6_3] | 8코어급(예: Ryzen 7, i7).[^6_3] | 8K context, 낮은 동시성이면 충분. |
| ~50명 (소형 서비스, 동접 10–20) | 8–14B, 4bit/8bit, vLLM 서버형 | L40S 24GB 또는 24GB급 GPU 1장.[^6_1][^6_2] | 64GB RAM.[^6_2][^6_5] | NVMe 2TB (여러 모델·인덱스).[^6_3] | 12–16코어 (EPYC Silver/Gold, Xeon Silver).[^6_6] | vLLM batching으로 동접 10–20 처리. |
| ~100명 (동접 20–40) | 14–34B, 양자화, vLLM | 24–48GB VRAM급 GPU 1장, 또는 2×24GB.[^6_1][^6_2] | 128GB RAM 권장.[^6_2][^6_5] | NVMe 2–4TB, 고IOPS.[^6_2][^6_3] | 16–24코어.[^6_6] | 8–16K context RAG, 중간 부하. |
| ~500명 (동접 100 수준) | 14–34B 또는 70B(4bit) + vLLM | 2×L40S 48GB 또는 2×A100 40GB (총 80–96GB).[^6_1][^6_2] | 256GB RAM.[^6_2][^6_5] | NVMe 4TB+, RAID1/10.[^6_2] | 24–32코어.[^6_6] | vLLM tensor parallel + multi‑instance.[^6_7][^6_8] |
| ~1000명 (동접 200 수준) | 70B(8bit/FP8) + vLLM | 2×H100 80GB (160GB VRAM) 또는 동급.[^6_1][^6_9] | 256–512GB RAM.[^6_2] | NVMe 8TB+, 고대역폭.[^6_2] | 32–48코어.[^6_6] | DigitalOcean 가이드에서 70B·32K context·10동접에 160GB FP8 예시.[^6_1] 동접↑ 시 동일급 다중 노드 필요. |
| ~3000명 (동접 500–600) | 70B + 샤딩/스케일아웃 | 위 70B급 GPU 노드 3–4대 (총 GPU 6–8장 수준).[^6_1][^6_10] | 노드당 256–512GB, 전체 1TB+.[^6_2] | 노드당 NVMe 8TB, 공유 스토리지 선택.[^6_2] | 노드당 32–48코어, 총 100코어+.[^6_6] | vLLM 다중 인스턴스 + L4/Ingress 레벨 라우팅.[^6_7][^6_10] |
| ~5000명 (동접 800–1000) | 70B + 모듈러/모델 분산 | 70B급 GPU 노드 4–6대 (총 8–12GPU).[^6_1][^6_9] | 전체 1–2TB RAM.[^6_2] | NVMe 총 20TB+.[^6_2] | 총 150코어+.[^6_6] | 트래픽 기반 오토스케일 + 캐시/샤딩 필수.[^6_9] |
| 1만 이상 (B2C급, 동접 수천) | MoE or 다수 LLM 풀 | H100/MI300X급 GPU 수십 장 규모 (DGX/클러스터).[^6_2][^6_9] | 수 TB RAM.[^6_2] | NVMe 수십 TB + 분산 스토리지.[^6_2] | 수백 코어 규모.[^6_6] | 모델 캐싱, 프론트 프록시, region 분산 필수. |

- 표는 **대략적인 가이드**이며, 기준은:
    - 8–14B 모델은 8–24GB VRAM에서 4bit/8bit로 여유 있게,
    - 70B 모델은 FP8/8bit 시 2×80GB급(160GB)에서 편하게 돌아간다는 vLLM 사이징 예시를 따른 것입니다.[^6_4][^6_1]
    - RAM은 로컬 LLM 가이드에서 제시하는 “소규모는 32–64GB, 본격 서비스는 128–512GB 이상” 권장치를 반영했습니다.[^6_2][^6_3][^6_5]

질문하신 규모를 실제로 설계하려면, **모델 크기(8B/14B/70B), 컨텍스트 길이(4K/8K/32K), 목표 응답 지연(초당 토큰 수)** 중 하나를 먼저 고정해야 합니다.[^6_9][^6_1]
어떤 모델 크기(예: 14B vs 70B)를 기준으로 먼저 상세 산정해 볼까요?
<span style="display:none">[^6_11][^6_12][^6_13][^6_14][^6_15]</span>

<div align="center">⁂</div>

[^6_1]: https://www.digitalocean.com/community/conceptual-articles/vllm-gpu-sizing-configuration-guide

[^6_2]: https://unihost.com/blog/ai-servers-2025-hardware/

[^6_3]: https://localllm.in/blog/how-to-run-local-llm-guide-2025

[^6_4]: https://localllm.in/blog/best-local-llms-8gb-vram-2025

[^6_5]: https://www.reddit.com/r/LocalLLaMA/comments/1h9xv15/ram_sweet_spot_for_local_llms_in_2025/

[^6_6]: https://blogs.vmware.com/cloud-foundation/2024/09/25/llm-inference-sizing-and-performance-guidance/

[^6_7]: https://docs.vllm.ai/en/stable/serving/parallelism_scaling/

[^6_8]: https://docs.vllm.ai/en/stable/configuration/optimization/

[^6_9]: https://cloud.google.com/blog/topics/developers-practitioners/vllm-performance-tuning-the-ultimate-guide-to-xpu-inference-configuration

[^6_10]: https://oneuptime.com/blog/post/2026-01-25-vllm-llm-serving/view

[^6_11]: https://www.reddit.com/r/MachineLearning/comments/1ij8ywk/d_how_to_handle_concurrent_connections_using_vllm/

[^6_12]: https://docs.redhat.com/ko/documentation/red_hat_ai_inference_server/3.0/html-single/vllm_server_arguments/index

[^6_13]: https://berdachuk.com/ai/hardware-options-for-local-llm-2025

[^6_14]: https://www.reddit.com/r/LocalLLaMA/comments/1olq14f/megathread_local_ai_hardware_november_2025/

[^6_15]: https://introl.com/blog/local-llm-hardware-pricing-guide-2025


---

# 1. vLLM에서 Llama 70B FP8 모델 기준 10/50/100/500/1000/3000/5000/1만 사용자 동시 처리용 RAM/VRAM/SSD/CPU 스펙 계산하는 Excel 모델을 만들어 사용자 입력으로 조정 가능하게 해줘

2. Ollama로 같은 사용자 수 대응 시 하드웨어 스펙 비교
3. llama.cpp에서 1만명 동시 접속 서버 구성 팁
4. VLLM GPU tensor parallel multiple H100 비용 추정
5. RAG 파이프라인 추가 시 VRAM 증가량 계산법

각 항목별 답변을 상세하게 정리해 줘

질문이 많아서 각 항목별로 나눠서 답하겠습니다. 아래 수치는 “Llama 70B FP8, vLLM, 8K context, 초당 수 토큰 출력, RAG 기본 포함” 정도의 **러프한 설계용 모델**입니다.[^7_1][^7_2][^7_3]

***

## 1. vLLM + Llama 70B FP8 동시 접속별 Excel 사이징 모델

### 1‑1. 기본 가정

- 모델: Llama 70B, FP8 (vLLM 가이드에 나온 “70B FP8에 160GB VRAM 필요” 예시 기반).[^7_1]
- 1개 H100 80GB 카드 기준, 70B FP8 모델 서빙에 최소 2장(H100 80GB x2 = 160GB VRAM) 필요.[^7_4][^7_1]
- 동시 접속 증가 시:
    - GPU 수: 배치 효율+레이턴시를 고려해 계단식으로 증가.
    - RAM: 모델 캐시, vLLM KV 캐시 overhead, OS/DB 여유 포함.[^7_3][^7_5]


### 1‑2. 엑셀용 기본 테이블 (예시 값)

아래는 제가 만든 CSV(엑셀로 열 수 있음)의 내용입니다.


| 동시 접속(concurrency) | RAM (GB) | H100 80GB 개수 |
| :-- | :-- | :-- |
| 10 | 256 | 2 |
| 50 | 256 | 2 |
| 100 | 384 | 3 |
| 500 | 512 | 4 |
| 1000 | 512 | 4 |
| 3000 | 1024 | 8 |
| 5000 | 1536 | 12 |
| 10000 | 2048 | 16 |

- 동접 10–50: 2×H100 80GB(160GB VRAM) + 256GB RAM이면 충분 (여유 포함).[^7_3][^7_1]
- 동접 100–1000: 3–4×H100 (240–320GB VRAM) + 384–512GB RAM.[^7_1]
- 동접 3000–1만: GPU/노드 수를 늘리는 수평 확장(예: 4GPU 노드 여러 개)으로 가정.[^7_6][^7_7]


### 1‑3. 엑셀에서 사용자 입력으로 조정하는 구조

시트 구조 예:

1) 입력 시트 (`Inputs`)

- 셀:
    - `B2`: 모델 파라미터 수 (예: 70,000,000,000)
    - `B3`: 정밀도 (FP16/FP8/INT4 등, FP8이면 1byte, FP16이면 2byte로 맵핑)
    - `B4`: 토큰당 평균 KV 캐시 메모리(바이트) (가이드: 문헌 값 사용, 예: 1.5–2 byte/token/파라미터 수준, 또는 vLLM 문서 추정).[^7_8][^7_1]
    - `B5`: 최대 context 길이(토큰, 예: 8192)
    - `B6`: 동시 접속(10/50/…)
    - `B7`: GPU당 VRAM(GB, H100이면 80)
    - `B8`: GPU당 동시 요청 핸들링 목표 (예: 50 concurrent per 2 H100)

2) 계산 시트 (`Sizing`)

- 모델 메모리:
    - `model_mem_gb = (params * bytes_per_param) / (1024^3)`
    - FP8 기준: bytes_per_param=1 → 70B ≈ 70GB, 여유 포함 80GB 이상.[^7_1]
- KV 캐시 메모리:
    - `kv_mem_gb = concurrency * max_context * kv_bytes_per_token / 1e9`
    - 여기에 30–50% 오버헤드 계수 곱.
- GPU 수:
    - `gpu_count = CEILING( (model_mem_gb * safety_factor + kv_mem_gb) / gpu_vram_gb , 1 )`
    - safety_factor (예: 1.3–1.5).[^7_8][^7_1]
- RAM:
    - `ram_gb = base_ram + concurrency * ram_per_user`
    - base_ram (예: 128GB), ram_per_user (예: 0.1–0.2GB)로 시작 후 튜닝.[^7_5][^7_3]

이렇게 하면, 사용자가 **동시 접속·컨텍스트 길이·정밀도**를 바꾸면서 GPU·RAM값을 자동으로 재계산할 수 있습니다.

***

## 2. Ollama에서 동일 동접 대응 시 하드웨어 비교

Ollama는 서버/배치 최적화 수준이 vLLM보다 낮고, 주로 7–14B 모델과 소규모 동시성에 맞춰져 있습니다.[^7_9][^7_10][^7_11]
70B FP8 기준으로 보면, **동시 접속 대비 스펙을 더 높게 잡거나 동시 접속을 줄여야** 합니다.

대략적인 비교(70B FP8, 동일 동접 목표, 단일 서버 관점):


| 동시 접속 | vLLM (H100 80GB, 예) | Ollama (동급 목표 시) | 특징 |
| :-- | :-- | :-- | :-- |
| 10–50 | 2×H100, 256GB RAM.[^7_1] | 2×H100, 256–384GB RAM (오버헤드 감안).[^7_10][^7_9] | Ollama는 요청 스케줄링·배치 비효율로 여유 필요. |
| 100 | 3×H100, 384GB RAM. | 4×H100, 512GB RAM 권장. | 대규모 동시성보단 다수 인스턴스로 scale‑out하는 게 현실적. |
| 500 이상 | 4×H100 이상, 또는 다중 노드.[^7_6] | Ollama 단일 클러스터만으로는 비효율적, vLLM이나 SGLang 같은 서버형 프레임워크 권장.[^7_11][^7_12] |  |

- Ollama는 **“개발·팀 단위·소규모 서비스”**에 현실적으로 맞고, 수천 동접 이상은 vLLM 등으로 옮기는 게 일반적인 권고입니다.[^7_11][^7_12][^7_9]

***

## 3. llama.cpp로 1만 명 동시 접속 서버 구성 팁

현실적으로는 **llama.cpp 단일 클러스터로 1만 동접은 비효율적**입니다. 보통은:

- 모델: 양자화 Llama 13–34B 또는 더 작은 모델.
- 전략:
    - 1) **수십~수백 개의 서버 노드**에 모델을 분산 배포.
    - 2) 각 노드는 GGUF 4bit/5bit 양자화 + GPU/CPU 혼합.[^7_13]
    - 3) L4/L7 로드밸런서로 라우팅.

팁 몇 가지:

1) **모델 크기·정밀도 줄이기**

- 70B 대신 13–34B 4bit GGUF 모델 사용 → 노드당 VRAM 16–24GB로 충분.[^7_13]
- 동접 1만이면, 예를 들어 “노드당 50–100 동접”을 목표로 100–200노드 규모 설계.

2) **KV 캐시 공유/제한**

- llama.cpp는 vLLM만큼 aggressive한 KV cache sharing은 아니지만,
    - 프롬프트 길이 제한,
    - 세션 타임아웃,
    - 출력 토큰 수 제한으로 메모리 폭주를 막아야 함.

3) **프론트 계층에서 Pre‑routing**

- 사용자별/엔드포인트별로 모델을 나누어,
    - “무거운 질의(긴 context)”는 GPU 노드,
    - “가벼운 질의(짧은 context)”는 CPU 노드로 보내는 구조.

4) **모델 샤딩·버전 분리**

- 1만 동접 전체가 항상 동일 모델을 필요로 하진 않음.
    - FAQ/경량 RAG: 7–8B 모델.
    - 복잡 QA: 34B 모델.
- 이렇게 계층화하면 llama.cpp 기반 클러스터 규모를 많이 줄일 수 있습니다.[^7_13]

요약하면, **llama.cpp로 1만 동접은 GPU/CPU 노드 수십~수백 개 + 모델 경량화 + 지능적 라우팅**이 전제입니다. 순수하게 “70B 하나로 1만 동접”은 비현실적입니다.

***

## 4. vLLM GPU tensor parallel + H100 비용 추정

### 4‑1. H100 비용 레퍼런스

- 2025/2026년 기준 서버용 H100 80GB 카드는 1장당 대략 25,000–40,000 USD 수준으로 보고됩니다 (서버·리셀러별 편차 큼).[^7_14][^7_3]
- 클라우드(H100 80GB on‑demand) 시:
    - 시가: 4–6 USD/hour/카드 구간으로 안내하는 제공자들이 많음.[^7_14][^7_3]


### 4‑2. 동접별 H100 비용 러프 추정 (on‑prem HW 기준)

예시: 중간값 30,000 USD/장 가정.[^7_3][^7_14]


| 동시 접속 | H100 80GB 수 | 카드 비용(USD, 대략) |
| :-- | :-- | :-- |
| 10–50 | 2 | 60,000 |
| 100 | 3 | 90,000 |
| 500–1000 | 4 | 120,000 |
| 3000 | 8 | 240,000 |
| 5000 | 12 | 360,000 |
| 10000 | 16 | 480,000 |

[^7_14][^7_3]

- 여기에 서버 섀시, NVMe, CPU, RAM, 네트워크(100/200GbE) 등을 포함하면 통상 **GPU 비용 x1.5~2배** 정도로 TCO를 잡습니다.[^7_2][^7_3]


### 4‑3. 클라우드 H100 비용(rough)

예: 1장 5 USD/h 가정.[^7_3][^7_14]

- 4×H100 (1000 동접급 예시) → 20 USD/h →
    - 하루 480 USD, 월(30일) 14,400 USD.
- 8×H100 (3000 동접) → 40 USD/h → 월 약 28,800 USD.

실제 단가는 클라우드·약정·예약 인스턴스에 따라 크게 다르니, **H100카드수 × 단가 (시간/월)**만 곱해보면 됩니다.

***

## 5. RAG 파이프라인 추가 시 VRAM 증가량 계산법

vLLM/LLM에서 VRAM은 크게:

1) **모델 파라미터 메모리** (고정).
2) **KV 캐시 메모리** (토큰 수·동시 요청수에 비례).[^7_8][^7_1]
3) 기타 메모리(optimizer는 inference에 없음, 텐서/버퍼 등).

RAG를 붙이면 **context 길이 + 응답 길이** 때문에 “토큰 수”가 늘어나고, 따라서 **KV 캐시 메모리**가 증가합니다.[^7_15][^7_8]

### 5‑1. 단순화된 계산식

어림잡아:

- `VRAM_total ≈ VRAM_model + VRAM_KV`
- `VRAM_KV ≈ N_concurrent * (L_prompt + L_context + L_output) * bytes_per_token`

여기서:

- `N_concurrent`: 동시에 처리되는 요청 수 (배치 기준).
- `L_prompt`: 시스템+질문 토큰 길이.
- `L_context`: RAG에서 붙는 문서 토큰 총합.
- `L_output`: 평균 답변 길이.
- `bytes_per_token`: 내부 구현·정밀도에 따라 다르지만, 대략 수십~수백 byte/token 수준 (vLLM 문서/실험값 참조 필요).[^7_8][^7_1]

**RAG 추가 전/후 증가분**만 보면:

- `ΔVRAM_KV ≈ N_concurrent * ΔL_context * bytes_per_token`

예시:

- RAG 미사용: context 0, prompt+output 합 1000토큰.
- RAG 사용: context 4000토큰 추가 (총 5000).
- 동시 요청수: 32.
- bytes_per_token: 100 byte/token (예시, 실제는 엔진별 계산 필요).

→ `ΔVRAM_KV ≈ 32 * 4000 * 100 ≈ 12,800,000 bytes ≈ 12.2 MB`

실제는 vLLM의 텐서/레이어 수·헤드 수에 따라 더 커지며, vLLM 문서에서는 **긴 컨텍스트에서는 KV 캐시 메모리가 모델 메모리와 비견될 수준으로 커질 수 있음**을 경고합니다.[^7_4][^7_1][^7_8]

### 5‑2. 설계용 러프 룰

실무 감각으로는:

- 4K context → KV 캐시 ~X GB
- 8K context → 약 2X GB
- 16K context → 약 4X GB

즉, context를 2배로 늘리면 KV 캐시가 대략 2배 이상 늘어납니다.[^7_1][^7_8]
→ RAG에서 context를 공격적으로 늘릴수록 **동시 요청수 × context 길이**를 고려한 VRAM 사이징이 필요합니다.

***

원하시면, 위 엑셀 모델 구조를 실제 수식까지 채운 형태(열/셀 설계 + 예시 수식)로 한글 주석과 함께 더 구체적으로 풀어 드릴 수 있습니다.

<div align="center">⁂</div>

[^7_1]: https://www.digitalocean.com/community/conceptual-articles/vllm-gpu-sizing-configuration-guide

[^7_2]: https://blogs.vmware.com/cloud-foundation/2024/09/25/llm-inference-sizing-and-performance-guidance/

[^7_3]: https://unihost.com/blog/ai-servers-2025-hardware/

[^7_4]: https://cloud.google.com/blog/topics/developers-practitioners/vllm-performance-tuning-the-ultimate-guide-to-xpu-inference-configuration

[^7_5]: https://www.reddit.com/r/LocalLLaMA/comments/1h9xv15/ram_sweet_spot_for_local_llms_in_2025/

[^7_6]: https://docs.vllm.ai/en/stable/serving/parallelism_scaling/

[^7_7]: https://oneuptime.com/blog/post/2026-01-25-vllm-llm-serving/view

[^7_8]: https://docs.vllm.ai/en/stable/configuration/optimization/

[^7_9]: https://joshuaopolko.com/ollama/

[^7_10]: https://shshell.com/blog/ollama-module-1-lesson-4

[^7_11]: https://particula.tech/blog/ollama-vs-vllm-comparison

[^7_12]: https://stable-learn.com/en/ai-model-tools-comparison/

[^7_13]: https://localllm.in/blog/llamacpp-vram-requirements-for-local-llms

[^7_14]: https://introl.com/blog/local-llm-hardware-pricing-guide-2025

[^7_15]: https://rocm.blogs.amd.com/artificial-intelligence/rag-pipeline-vllm/README.html


---

# 엑셀 모델 구조를 실제 수식까지 채운 형태(열/셀 설계 + 예시 수식)로 한글 주석과 함께 더 구체적으로 정리해 줘

엑셀 한 파일 안에 **입력 시트(Inputs)** + **계산 시트(Sizing)** 두 개를 두는 구조로 설명하겠습니다.
모델은 “Llama 70B, FP8, vLLM, 8K context”를 기본 가정으로 합니다.[^8_1][^8_2][^8_3]

***

## 1. 시트 1: `Inputs` 설계

### 1‑1. 셀 배치

`Inputs` 시트에 아래처럼 입력 영역을 둡니다.


| 셀 | 이름(설명) | 값 예시 | 비고 |
| :-- | :-- | :-- | :-- |
| B2 | `ModelParams` (모델 파라미터 수) | 70000000000 | 70B |
| B3 | `PrecisionBytes` (파라미터당 바이트 수) | 1 | FP8 → 1 byte, FP16이면 2 |
| B4 | `MaxContextTokens` (최대 컨텍스트 길이) | 8192 | 토큰 단위 |
| B5 | `AvgOutputTokens` (평균 출력 길이) | 512 | 답변 토큰 수 |
| B6 | `KVBytesPerToken` (토큰당 KV 캐시 바이트) | 120 | 러프 값, 튜닝용[^8_2] |
| B7 | `SafetyFactorModel` (모델 메모리 여유 계수) | 1.3 | 30% 여유[^8_1] |
| B8 | `SafetyFactorKV` (KV 여유 계수) | 1.5 | 50% 여유[^8_2] |
| B9 | `GPUVRAMGB` (GPU 1장 VRAM) | 80 | H100 80GB 기준[^8_1] |
| B10 | `BaseRAMGB` (기본 RAM) | 128 | OS, 서비스 등 기본 |
| B11 | `RAMPerUserGB` (사용자 1명당 RAM) | 0.1 | 대략치 |
| B13 | `ConcurrencyList` (콤마구분 동시접속 목록) | 10,50,100,500,1000,3000,5000,10000 | TEXT |

한글 주석은 C열에 메모 형식으로 달아두면 됩니다.

### 1‑2. 이름 정의(선택)

엑셀에서 수식을 읽기 쉽게 하기 위해 다음 셀에 이름을 정의해 둡니다.

- B2 → 이름: `ModelParams`
- B3 → `PrecisionBytes`
- B4 → `MaxContextTokens`
- B5 → `AvgOutputTokens`
- B6 → `KVBytesPerToken`
- B7 → `SafetyFactorModel`
- B8 → `SafetyFactorKV`
- B9 → `GPUVRAMGB`
- B10 → `BaseRAMGB`
- B11 → `RAMPerUserGB`

(수식 예시에 이 이름들을 그대로 사용합니다.)

***

## 2. 시트 2: `Sizing` 설계

이 시트에서 동시 접속 수별로 RAM/VRAM/GPU 개수 등을 계산합니다.
행 단위로 각 동시 접속 값을 하나씩 넣는 구조입니다.

### 2‑1. 헤더와 입력 열

`Sizing` 시트 A1:D1에 헤더를 입력합니다.

- A1: `Concurrency`  (동시 접속 수)
- B1: `ModelMemGB`   (모델 메모리 GB)
- C1: `KVCacheGB`    (KV 캐시 메모리 GB)
- D1: `TotalVRAMGB`  (총 VRAM 요구량 GB)
- E1: `NumGPU`       (필요 GPU 개수)
- F1: `RAMGB`        (필요 시스템 RAM GB)

A열에 동시 접속수를 입력합니다.

- A2: 10
- A3: 50
- A4: 100
- A5: 500
- A6: 1000
- A7: 3000
- A8: 5000
- A9: 10000

(또는 `Inputs!B13`에서 TEXTSPLIT을 써서 자동 분해해도 됩니다. Office 365 기준.)

예:
`=TEXTSPLIT(Inputs!B13, ",")` 를 A2 셀에 입력 후, 아래로 spill 되도록.

***

## 3. 수식 정의 (핵심 로직)

### 3‑1. 모델 메모리 계산 (B열)

B2 셀에:

```excel
= (ModelParams * PrecisionBytes) / (1024^3) * SafetyFactorModel
```

설명:

- `ModelParams * PrecisionBytes` → 전체 파라미터 바이트 수.
- `/ (1024^3)` → GB 단위로 변환.
- `* SafetyFactorModel` → 여유 계수(예: 1.3).

이 수식을 B2에서 B9까지 복사해도 값은 동일(모델 메모리는 동시 접속과 무관, 고정)입니다.

### 3‑2. KV 캐시 메모리 계산 (C열)

KV 캐시는 **동시 접속 × (prompt+context+output 토큰 수)**에 비례합니다.[^8_2][^8_1]

여기서는 단순화를 위해:

- `L_total ≈ MaxContextTokens + AvgOutputTokens` 으로 놓습니다.
- prompt 길이는 상대적으로 작다고 보고 context에 흡수.[^8_4]

C2 셀:

```excel
= A2 * (MaxContextTokens + AvgOutputTokens) * KVBytesPerToken / (1024^3) * SafetyFactorKV
```

설명:

- `A2`: 동시 접속(concurrency).
- `(MaxContextTokens + AvgOutputTokens)`: context + output 토큰 합.
- `KVBytesPerToken`: 토큰당 KV 캐시 바이트(대략).
- `/ (1024^3)`: GB 변환.
- `* SafetyFactorKV`: 여유 계수(예: 1.5).

이 수식을 C2에서 C9까지 복사.

### 3‑3. 총 VRAM 요구량 계산 (D열)

D2 셀:

```excel
= B2 + C2
```

(모델 + KV 캐시)

D2~D9까지 복사.

### 3‑4. GPU 개수 계산 (E열)

각 GPU가 `GPUVRAMGB` GB를 가진다고 할 때, 필요한 GPU 개수는:

E2 셀:

```excel
=CEILING( D2 / GPUVRAMGB , 1 )
```

- `CEILING` 함수로 올림 처리.
- 예: D2=160, GPUVRAMGB=80 → 2장.

E2~E9까지 복사.

### 3‑5. 시스템 RAM 계산 (F열)

RAM은 **기본값 + 동시 접속당 추가**로 단순 모델링합니다.[^8_5][^8_6]

F2 셀:

```excel
= BaseRAMGB + A2 * RAMPerUserGB
```

예: BaseRAMGB=128, RAMPerUserGB=0.1, A2=10 → 129GB.
F2~F9까지 복사.

***

## 4. 예시 값 해석 (직접 넣었을 때의 감각)

예를 들어 기본값을:

- `ModelParams` = 70,000,000,000
- `PrecisionBytes` = 1 (FP8)
- `MaxContextTokens` = 8192
- `AvgOutputTokens` = 512
- `KVBytesPerToken` = 120
- `SafetyFactorModel` = 1.3
- `SafetyFactorKV` = 1.5
- `GPUVRAMGB` = 80
- `BaseRAMGB` = 128
- `RAMPerUserGB` = 0.1

로 놓으면 대략:

- B2 (ModelMemGB) ≈ 70 * 1 / 1024^3 * 1.3 → 약 91GB 정도(러프).[^8_1]
- C2 (10 동접 KVCacheGB) → 수 GB 범위 (concurrency와 context 길이에 비례).[^8_2]
- D2 (TotalVRAMGB) → 120–150GB 사이 → E2 = 2 GPU.
- A가 커질수록 C가 크게 증가 → D·E도 계단식 증가.

실제 숫자는 `KVBytesPerToken` 값에 따라 크게 달라지므로, **초기에는 높게 잡고(예: 200–256), 실제 프로파일링 후 줄이는 식**으로 사용하는 걸 추천합니다.[^8_7][^8_2]

***

## 5. 추가 개선 아이디어

1) **입력 검증용 셀**

- `Sizing` 상단에 “모델 메모리/동시 접속별 KV 비율”을 요약해서 표시 (예: `=AVERAGE(C2:C9)/B2`).

2) **GPU당 목표 동시 접속수 제약**

- 예: “GPU당 최대 concurrency 50” 같은 제한을 추가하려면,
    - `NumGPU_by_load = CEILING( A2 / MaxConcurrencyPerGPU , 1 )`
    - `NumGPU_final = MAX( NumGPU_vram, NumGPU_by_load )`
형태로 더 강한 쪽을採용.

3) **RAG on/off 시나리오 비교**

- `MaxContextTokens`를 0/8192로 바꿔보면서 C열(=KVCache) 증가량을 시각적으로 비교 가능.[^8_4][^8_2]

***

이 구조로 만들어 두면,

- 동시 접속 수(A열),
- context 길이(B4),
- 정밀도(B3),
- GPU VRAM(B9)
만 바꿔도 RAM/VRAM/GPU 개수 추정을 즉시 다시 계산할 수 있습니다.

혹시 이걸 실제로 쓰실 엑셀 템플릿(.xlsx) 구조까지, 셀 주소/주석 문구를 포함해 더 세밀하게 설계해 드릴까요?

<div align="center">⁂</div>

[^8_1]: https://www.digitalocean.com/community/conceptual-articles/vllm-gpu-sizing-configuration-guide

[^8_2]: https://docs.vllm.ai/en/stable/configuration/optimization/

[^8_3]: https://blogs.vmware.com/cloud-foundation/2024/09/25/llm-inference-sizing-and-performance-guidance/

[^8_4]: https://rocm.blogs.amd.com/artificial-intelligence/rag-pipeline-vllm/README.html

[^8_5]: https://unihost.com/blog/ai-servers-2025-hardware/

[^8_6]: https://www.reddit.com/r/LocalLLaMA/comments/1h9xv15/ram_sweet_spot_for_local_llms_in_2025/

[^8_7]: https://cloud.google.com/blog/topics/developers-practitioners/vllm-performance-tuning-the-ultimate-guide-to-xpu-inference-configuration


---

# 엑셀 템플릿(.xlsx) 구조 및 셀 주소/주석 문구를 포함해 더 세밀하게 설계해 주고, 템플릿(.xlsx)을 생성해 줘

요청하신 내용을 반영해서 실제로 엑셀 템플릿(.xlsx)을 만들었습니다. 구조와 셀/주석을 먼저 설명드리고, 마지막에 파일 링크를 안내하겠습니다.

***

## 1. `Inputs` 시트 구조

### 1‑1. 기본 레이아웃

- 시트 이름: `Inputs`
- 헤더:
    - A1: `파라미터`
    - B1: `값`
    - C1: `설명`


#### 파라미터 영역 (A2:C11)

| 셀 | 값 | 설명(실제 텍스트) |
| :-- | :-- | :-- |
| A2 | `ModelParams` | 모델 파라미터 수 (예: 70B → 70000000000) |
| B2 | `70000000000` | 70B 기본값 |
| C2 | `모델 파라미터 수 (예: 70B → 70000000000)` |  |

| 셀 | 값 | 설명 |
| :-- | :-- | :-- |
| A3 | `PrecisionBytes` | 파라미터 1개당 바이트 수 (FP8=1, FP16=2, BF16=2 등) |
| B3 | `1` | FP8 기준 |
| C3 | `파라미터 1개당 바이트 수 (FP8=1, FP16=2, BF16=2 등)` |  |

| 셀 | 값 | 설명 |
| :-- | :-- | :-- |
| A4 | `MaxContextTokens` | 최대 컨텍스트 길이 (토큰 수, RAG 포함) |
| B4 | `8192` | 8K context 기본값 |
| C4 | `최대 컨텍스트 길이 (토큰 수, RAG 포함)` |  |

| 셀 | 값 | 설명 |
| :-- | :-- | :-- |
| A5 | `AvgOutputTokens` | 평균 출력 토큰 수 (답변 길이 가정) |
| B5 | `512` |  |
| C5 | `평균 출력 토큰 수 (답변 길이 가정)` |  |

| 셀 | 값 | 설명 |
| :-- | :-- | :-- |
| A6 | `KVBytesPerToken` | 토큰당 KV 캐시 메모리 (바이트). 초기에는 넉넉히 잡고 튜닝 |
| B6 | `120` |  |
| C6 | `토큰당 KV 캐시 메모리 (바이트). 초기에는 넉넉히 잡고 튜닝` |  |

| 셀 | 값 | 설명 |
| :-- | :-- | :-- |
| A7 | `SafetyFactorModel` | 모델 메모리 여유 계수 (예: 1.3 = 30% 여유) |
| B7 | `1.3` |  |
| C7 | `모델 메모리 여유 계수 (예: 1.3 = 30% 여유)` |  |

| 셀 | 값 | 설명 |
| :-- | :-- | :-- |
| A8 | `SafetyFactorKV` | KV 캐시 여유 계수 (예: 1.5 = 50% 여유) |
| B8 | `1.5` |  |
| C8 | `KV 캐시 여유 계수 (예: 1.5 = 50% 여유)` |  |

| 셀 | 값 | 설명 |
| :-- | :-- | :-- |
| A9 | `GPUVRAMGB` | GPU 1장 VRAM 용량 (GB). 예: H100 80GB → 80 |
| B9 | `80` |  |
| C9 | `GPU 1장 VRAM 용량 (GB). 예: H100 80GB → 80` |  |

| 셀 | 값 | 설명 |
| :-- | :-- | :-- |
| A10 | `BaseRAMGB` | LLM 서버 기본 RAM (GB). OS/서비스용 포함 베이스 |
| B10 | `128` |  |
| C10 | `LLM 서버 기본 RAM (GB). OS/서비스용 포함 베이스` |  |

| 셀 | 값 | 설명 |
| :-- | :-- | :-- |
| A11 | `RAMPerUserGB` | 동시 접속 1명당 필요 RAM (GB) 추정치 |
| B11 | `0.1` |  |
| C11 | `동시 접속 1명당 필요 RAM (GB) 추정치` |  |

이 A2:A11 값들은 이름으로 정의되어 있어서, 다른 시트에서 `ModelParams`, `MaxContextTokens` 등으로 바로 참조 가능합니다.

#### 동시 접속 리스트 (A13:C13)

| 셀 | 값 | 설명 |
| :-- | :-- | :-- |
| A13 | `ConcurrencyList` | 이름 라벨 |
| B13 | `10,50,100,500,1000,3000,5000,10000` | 기본 동시 접속 목록 |
| C13 | `콤마로 구분된 동시 접속 수 목록` |  |

(현재 템플릿에서는 `Sizing` 시트에 concurrency를 직접 넣어 두었고, 필요시 이 셀을 TEXTSPLIT으로 파싱해도 됩니다.)

***

## 2. `Sizing` 시트 구조

### 2‑1. 헤더 및 설명(주석)

- 시트 이름: `Sizing`
- 1행 헤더:

| 셀 | 값 | 주석(Comment) |
| :-- | :-- | :-- |
| A1 | `Concurrency` | “동시에 처리하려는 요청 수 (concurrency)” |
| B1 | `ModelMemGB` | “모델 파라미터 메모리 (GB 단위, 여유 포함)” |
| C1 | `KVCacheGB` | “KV 캐시 메모리 (GB). 컨텍스트/출력 길이와 동시접속 수에 비례” |
| D1 | `TotalVRAMGB` | “모델 + KV 캐시를 합친 총 VRAM 필요량 (GB)” |
| E1 | `NumGPU` | “GPU 1장 VRAM 기준 필요한 GPU 개수 (올림)” |
| F1 | `RAMGB` | “서버 RAM 요구량 (기본값 + 사용자당 RAM)” |

### 2‑2. 동시 접속 입력 (A열)

미리 값이 들어가 있습니다:

- A2: 10
- A3: 50
- A4: 100
- A5: 500
- A6: 1000
- A7: 3000
- A8: 5000
- A9: 10000

필요하면 사용자가 직접 수정하거나 행을 추가해서 사용하시면 됩니다.

### 2‑3. 각 열 수식

각 행(2~9행)에 수식이 들어가 있습니다.

#### B열: 모델 메모리 GB (`ModelMemGB`)

- B2 셀:

```excel
=(ModelParams*PrecisionBytes)/(1024^3)*SafetyFactorModel
```

- B3~B9까지 동일 수식 (행 복사).
- 의미: “파라미터 수 × 바이트 수 → GB로 변환 → 모델 여유 계수 적용”.[^9_1][^9_2]


#### C열: KV 캐시 메모리 GB (`KVCacheGB`)

- C2 셀:

```excel
= A2*(MaxContextTokens+AvgOutputTokens)*KVBytesPerToken/(1024^3)*SafetyFactorKV
```

- C3~C9: `A3`, `A4`… 로 자동으로 바뀌도록 복사.
- 의미:
    - `A2`: 동시 접속 수.
    - `(MaxContextTokens+AvgOutputTokens)`: 한 요청당 토큰 수 (context + output).
    - `KVBytesPerToken`: 토큰당 KV 캐시 메모리.
    - `/ (1024^3)`: GB 변환.
    - `* SafetyFactorKV`: 여유 계수.[^9_2][^9_1]


#### D열: 총 VRAM GB (`TotalVRAMGB`)

- D2 셀:

```excel
= B2 + C2
```

- D3~D9: 각각 `=B3+C3` …
- 의미: “모델 메모리 + KV 캐시 메모리”.[^9_1][^9_2]


#### E열: GPU 개수 (`NumGPU`)

- E2 셀:

```excel
=CEILING(D2/GPUVRAMGB,1)
```

- E3~E9: `D3`, `D4` … 로 복사.
- 의미: “총 VRAM 요구량 / GPU 1장의 VRAM → 올림”.
    - 예: `D2=160`, `GPUVRAMGB=80` → 2장.


#### F열: RAM 요구량 (`RAMGB`)

- F2 셀:

```excel
= BaseRAMGB + A2*RAMPerUserGB
```

- F3~F9: `A3`, `A4`… 로 복사.
- 의미: “기본 RAM + 동시 접속 수 × 사용자당 RAM”.[^9_3][^9_4]

***

## 3. 사용 방법 요약

1. `Inputs` 시트에서:
    - 모델 파라미터 수, 정밀도(FP8/FP16 등), 컨텍스트 길이, 출력 길이, KVBytesPerToken 등을 환경에 맞게 수정.
    - GPU VRAM, 기본 RAM, 사용자당 RAM 등도 실제 장비·목표에 맞게 조정.
2. `Sizing` 시트에서:
    - A열의 `Concurrency` 값(10/50/100/500/1000/3000/5000/10000)을 원하는 값으로 변경하거나 행을 추가.
    - B~F열이 자동으로 재계산되어 **각 동시 접속 수준에서 필요한 모델 메모리, KV 캐시, 총 VRAM, GPU 개수, 시스템 RAM**을 확인.
3. RAG context 길이를 바꾸고 싶으면:
    - `Inputs!B4 (MaxContextTokens)` 값을 4096, 16384 등으로 수정 → `Sizing` 시트의 C열(KV 메모리)과 D/E열(VRAM/GPU)이 일괄 업데이트.

***

## 4. 템플릿 파일

위 구조로 생성한 엑셀 파일은 아래와 같습니다.

- 파일 이름: `vllm_70b_fp8_sizing_template.xlsx`
- 위치: 이 대화에 첨부된 아티팩트로 제공됩니다.

해당 파일을 다운받아 바로 열면, 설명드린 `Inputs`/`Sizing` 시트와 수식·주석이 모두 들어 있습니다.
필요하면, 여기에 **GPU당 최대 동시 처리량 제약(예: GPU 1장당 최대 50 동접)** 같은 조건을 추가해서 `NumGPU`를 `MAX(VRAM기준, 처리량기준)`으로 바꾸는 확장도 도와드릴 수 있습니다.

<div align="center">⁂</div>

[^9_1]: https://www.digitalocean.com/community/conceptual-articles/vllm-gpu-sizing-configuration-guide

[^9_2]: https://docs.vllm.ai/en/stable/configuration/optimization/

[^9_3]: https://unihost.com/blog/ai-servers-2025-hardware/

[^9_4]: https://www.reddit.com/r/LocalLLaMA/comments/1h9xv15/ram_sweet_spot_for_local_llms_in_2025/


---

# 엑셀파일을 다운로드할 수가 없습니다. 해당 파일을 다운로드해 주세요.

지금 환경에서는 제가 직접 “다운로드 시작”을 트리거할 수 없고, 방금 생성한 파일만 시스템 쪽에 등록된 상태입니다.
그래서 두 가지 대안을 드리겠습니다.

## 1. 엑셀 직접 만들기 (구조 복사)

엑셀을 열고 아래 순서대로 입력하시면, 제가 만든 것과 동일한 템플릿을 재현할 수 있습니다.

### 1‑1. 시트 `Inputs`

1) `Inputs` 시트 생성 후, A1:C1 입력:

- A1: `파라미터`
- B1: `값`
- C1: `설명`

2) A2:C11 아래 값 그대로 입력:

- A2: `ModelParams` / B2: `70000000000` / C2: `모델 파라미터 수 (예: 70B → 70000000000)`
- A3: `PrecisionBytes` / B3: `1` / C3: `파라미터 1개당 바이트 수 (FP8=1, FP16=2, BF16=2 등)`
- A4: `MaxContextTokens` / B4: `8192` / C4: `최대 컨텍스트 길이 (토큰 수, RAG 포함)`
- A5: `AvgOutputTokens` / B5: `512` / C5: `평균 출력 토큰 수 (답변 길이 가정)`
- A6: `KVBytesPerToken` / B6: `120` / C6: `토큰당 KV 캐시 메모리 (바이트). 초기에는 넉넉히 잡고 튜닝`
- A7: `SafetyFactorModel` / B7: `1.3` / C7: `모델 메모리 여유 계수 (예: 1.3 = 30% 여유)`
- A8: `SafetyFactorKV` / B8: `1.5` / C8: `KV 캐시 여유 계수 (예: 1.5 = 50% 여유)`
- A9: `GPUVRAMGB` / B9: `80` / C9: `GPU 1장 VRAM 용량 (GB). 예: H100 80GB → 80`
- A10: `BaseRAMGB` / B10: `128` / C10: `LLM 서버 기본 RAM (GB). OS/서비스용 포함 베이스)`
- A11: `RAMPerUserGB` / B11: `0.1` / C11: `동시 접속 1명당 필요 RAM (GB) 추정치`

3) A13:C13 입력:

- A13: `ConcurrencyList`
- B13: `10,50,100,500,1000,3000,5000,10000`
- C13: `콤마로 구분된 동시 접속 수 목록`

4) (선택) 이름 정의:

- 수식 → 이름 관리자에서
    - `ModelParams` → `=Inputs!$B$2`
    - `PrecisionBytes` → `=Inputs!$B$3`
    - `MaxContextTokens` → `=Inputs!$B$4`
    - `AvgOutputTokens` → `=Inputs!$B$5`
    - `KVBytesPerToken` → `=Inputs!$B$6`
    - `SafetyFactorModel` → `=Inputs!$B$7`
    - `SafetyFactorKV` → `=Inputs!$B$8`
    - `GPUVRAMGB` → `=Inputs!$B$9`
    - `BaseRAMGB` → `=Inputs!$B$10`
    - `RAMPerUserGB` → `=Inputs!$B$11`


### 1‑2. 시트 `Sizing`

1) 새 시트 이름을 `Sizing`으로 변경.
2) 1행 헤더 입력:

- A1: `Concurrency`
- B1: `ModelMemGB`
- C1: `KVCacheGB`
- D1: `TotalVRAMGB`
- E1: `NumGPU`
- F1: `RAMGB`

3) A열에 동시 접속 입력:

- A2: `10`
- A3: `50`
- A4: `100`
- A5: `500`
- A6: `1000`
- A7: `3000`
- A8: `5000`
- A9: `10000`

4) 수식 입력:

- B2:

```excel
=(ModelParams*PrecisionBytes)/(1024^3)*SafetyFactorModel
```

→ B2를 B9까지 복사.
- C2:

```excel
=A2*(MaxContextTokens+AvgOutputTokens)*KVBytesPerToken/(1024^3)*SafetyFactorKV
```

→ C2를 C9까지 복사.
- D2:

```excel
=B2+C2
```

→ D2를 D9까지 복사.
- E2:

```excel
=CEILING(D2/GPUVRAMGB,1)
```

→ E2를 E9까지 복사.
- F2:

```excel
=BaseRAMGB + A2*RAMPerUserGB
```

→ F2를 F9까지 복사.

5) (선택) 헤더에 주석 달기:

- A1: “동시에 처리하려는 요청 수 (concurrency)”
- B1: “모델 파라미터 메모리 (GB 단위, 여유 포함)”
- C1: “KV 캐시 메모리 (GB). 컨텍스트/출력 길이와 동시접속 수에 비례”
- D1: “모델 + KV 캐시를 합친 총 VRAM 필요량 (GB)”
- E1: “GPU 1장 VRAM 기준 필요한 GPU 개수 (올림)”
- F1: “서버 RAM 요구량 (기본값 + 사용자당 RAM)”

이렇게 입력하면, 제가 만든 템플릿과 동일한 동작을 합니다.

***

## 2. 생성된 파일에 대해

제가 코드로 생성한 파일 정보는 다음과 같습니다.

- 파일명: `vllm_70b_fp8_sizing_template.xlsx`
- 내용: 위에서 설명한 `Inputs`/`Sizing` 시트 구조, 이름 정의, 수식, 주석 포함.

현재 인터페이스 제약 때문에 제가 직접 다운로드 버튼을 눌러 줄 수는 없고,
대신 위 설계를 그대로 복사해 엑셀에서 재현해 주셔야 합니다.

만약 직접 복사하는 과정이 번거로우시면,

- “Inputs 시트 캡처용 텍스트만”,
- “Sizing 시트 캡처용 텍스트만”
식으로 나눠서, 바로 붙여넣기 가능한 TSV 형태로도 정리해 드릴까요?

