<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# LLM history에 대해서 정리하고자 합니다. NLP부터 25년도 동향까지 논문 위주로 단계 및 주제별로 요약하고 리스트를 만들어 주세요

아래는 자연어처리(NLP)에서 최근(2025년) LLM(Large Language Model) 동향까지의 주요 발전 단계와 논문 중심의 주제별 요약 리스트입니다.

---

## NLP 및 LLM 역사: 단계 및 주제별 요약

### 1. 통계적 언어모델 (Statistical Language Models, SLM)

- **시기:** 1990년대
- **주요 논문/기술:**
    - n-gram, bigram, trigram 등 통계적 언어 모델
    - Markov 가정 기반의 다음 단어 예측
- **특징:**
    - 고정된 컨텍스트 길이(n)로 단어 예측
    - 정보 검색, 기계 번역 등에 활용
    - 차원의 저주(Curse of Dimensionality) 문제로 고차원 모델 한계[^1_2]


### 2. 신경망 기반 언어모델 (Neural Language Models, NLM)

- **시기:** 2000년대 후반~2010년대 초반
- **주요 논문/기술:**
    - RNN(Recurrent Neural Network): 시퀀스 데이터 처리[^1_8]
    - LSTM(Long Short-Term Memory): 장기 의존성 해결[^1_8]
    - Seq2Seq(Sequence-to-Sequence): 인코더-디코더 구조[^1_8]
- **특징:**
    - 신경망을 활용한 언어 모델링
    - 자연어 생성, 기계 번역 등 다양한 분야 적용


### 3. 사전학습 언어모델 (Pre-trained Language Models, PLM)

- **시기:** 2010년대 중반~말
- **주요 논문/기술:**
    - **Attention Mechanism:** "Neural Machine Translation by Jointly Learning to Align and Translate" (Bahdanau et al., 2015)[^1_8]
    - **Transformer:** "Attention Is All You Need" (Vaswani et al., 2017)[^1_7][^1_8]
    - **BERT:** "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding" (Devlin et al., 2018)
    - **GPT:** "Improving Language Understanding by Generative Pre-training" (Radford et al., 2018)[^1_7]
- **특징:**
    - Transformer 구조 도입으로 병렬 처리 및 성능 향상
    - 대규모 데이터로 사전 학습 후 미세조정(Fine-tuning) 가능
    - BERT(양방향), GPT(단방향) 등 다양한 아키텍처 등장


### 4. 대형 언어모델 (Large Language Models, LLM)

- **시기:** 2020년대 초~현재(2025)
- **주요 논문/기술:**
    - **GPT-3:** "Language Models are Few-Shot Learners" (Brown et al., 2020)
    - **LLaMA:** "LLaMA: Open and Efficient Foundation Language Models" (Meta, 2023)
    - **LLaMA 2:** (Meta, 2023)[^1_4][^1_7]
    - **GPT-4:** (OpenAI, 2023)
    - **최신 트렌드:** "Scaling RL with LLMs", "Can LLMs Plan?", "Hallucinations Improve LLMs in Drug Discovery" 등 (2025)[^1_3]
- **특징:**
    - 대규모 데이터 및 파라미터로 강력한 언어 이해/생성 능력
    - 다양한 도메인(로봇학습, 계획, 약물발견 등)으로 확장[^1_3][^1_5]
    - 오픈소스 LLM 활성화(LLaMA 등)[^1_4]
    - 한국어 특화 LLM 연구 증가[^1_4]

---

## 주요 논문 및 주제 리스트

| 단계 | 주요 논문/기술/주제 | 연도/시기 |
| :-- | :-- | :-- |
| SLM | n-gram, bigram, trigram, Markov 가정 | 1990년대 |
| NLM | RNN, LSTM, Seq2Seq | 2000~2010년대 |
| PLM | Attention, Transformer, BERT, GPT-1 | 2010년대 중후반 |
| LLM | GPT-3, LLaMA, LLaMA 2, GPT-4, 한국어 특화 LLM | 2020~2025년 |
| 최신 동향 | Scaling RL with LLMs, LLMs and Planning, Hallucinations in Drug Discovery | 2024~2025년 |


---

## 2025년 최신 연구 트렌드 요약

- **LLM의 다양한 응용:**
    - 로봇학습(RL), 계획, 약물발견, 행동 인식 등으로 확장[^1_3][^1_5]
- **성능 및 한계 분석:**
    - LLM의 능력, 한계, 다양한 상황에서의 성능 분석 논문 다수[^1_5]
- **모델 구조 및 경량화:**
    - 신경망 구조, 설계, 효율성, 연산 비용 최적화 연구[^1_5]
- **오픈소스 및 특화 모델:**
    - 오픈소스 LLM 생태계 확대, 한국어 등 특정 언어 특화 모델 연구[^1_4]

---

## 참고할 만한 논문 리스트(추가)

- **Attention Is All You Need** (Vaswani et al., 2017)
- **Improving Language Understanding by Generative Pre-training (GPT-1)** (Radford et al., 2018)
- **BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding** (Devlin et al., 2018)
- **Language Models are Few-Shot Learners (GPT-3)** (Brown et al., 2020)
- **LLaMA: Open and Efficient Foundation Language Models** (Meta, 2023)
- **LLaMA 2** (Meta, 2023)
- **최신 트렌드 논문:**
    - **Scaling RL with LLMs** (2025)
    - **Can LLMs Plan?** (2025)
    - **Hallucinations Improve LLMs in Drug Discovery** (2025)[^1_3]

---

이 리스트는 NLP의 역사와 최신 LLM 연구 동향을 논문 중심으로 정리한 것입니다.
각 단계별로 핵심 논문과 주제를 확인하시면 LLM의 발전 과정을 체계적으로 이해할 수 있습니다.
<span style="display:none">[^1_1][^1_10][^1_6][^1_9]</span>

<div align="center">⁂</div>

[^1_1]: https://hellollama.net/llm-의-발전과정-nlp-자연어처리-발전사/

[^1_2]: https://hayunjong83.tistory.com/58

[^1_3]: https://discuss.pytorch.kr/t/2025-01-20-01-27-ml-top-ml-papers-of-the-week/5993

[^1_4]: https://www.kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART002988606

[^1_5]: https://discuss.pytorch.kr/t/2024-09-30-10-06-ml-top-ml-papers-of-the-week/5300

[^1_6]: https://www.themoonlight.io/ko/review/history-development-and-principles-of-large-language-models-an-introductory-survey

[^1_7]: https://hodupy.tistory.com/2

[^1_8]: https://kyull-it.tistory.com/212

[^1_9]: https://discuss.pytorch.kr/t/2024-08-19-08-25-ml-top-ml-papers-of-the-week/5097

[^1_10]: https://highllight.tistory.com/231


---

# LLM 발전의 주요 논문 단계별 특징은 무엇인가요

LLM(Large Language Model)의 발전 단계별 주요 논문 및 특징은 아래와 같이 정리할 수 있습니다.

---

## 1. 통계적 언어모델(SLM): 1990년대

- **주요 논문/기술:**
    - n-gram, bigram, trigram 등 통계적 언어 모델
- **특징:**
    - Markov 가정에 기반한 예측(고정된 컨텍스트 길이로 다음 단어 예측)
    - 정보 검색 및 자연어처리 분야에서 성능 향상에 활용
    - 차원의 저주 문제로 인해 고차원 모델의 한계가 명확함[^2_1]

---

## 2. 신경망 언어모델(NLM): 2000년대 후반~2010년대 초반

- **주요 논문/기술:**
    - RNN(Recurrent Neural Network), LSTM(Long Short-Term Memory), Seq2Seq
- **특징:**
    - 신경망을 활용하여 시퀀스 데이터 처리 및 장기 의존성 문제 해결
    - 자연어 생성, 기계 번역 등 다양한 분야에 적용
    - 모델의 복잡도와 학습 데이터가 제한적임[^2_1][^2_2]

---

## 3. 사전학습 언어모델(PLM): 2010년대 중반~말

- **주요 논문/기술:**
    - **Attention Mechanism:** "Neural Machine Translation by Jointly Learning to Align and Translate" (Bahdanau et al., 2015)
    - **Transformer:** "Attention Is All You Need" (Vaswani et al., 2017)
    - **BERT:** "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding" (Devlin et al., 2018)
    - **GPT:** "Improving Language Understanding by Generative Pre-training" (Radford et al., 2018)
- **특징:**
    - Transformer 구조 도입으로 병렬 처리 및 성능 향상
    - 대규모 데이터로 사전 학습 후 미세조정(Fine-tuning) 가능
    - 다양한 NLP 작업에 범용적으로 적용 가능[^2_2][^2_5]

---

## 4. 대형 언어모델(LLM): 2020년대 초~2025년

- **주요 논문/기술:**
    - **GPT-3:** "Language Models are Few-Shot Learners" (Brown et al., 2020)
    - **LLaMA:** "LLaMA: Open and Efficient Foundation Language Models" (Meta, 2023)
    - **GPT-4:** (OpenAI, 2023)
    - **PaLM-E:** "An Embodied Multimodal Language Model" (2023)
    - **최신 트렌드:**
        - 강화학습(RLHF), 효율적 메모리 시스템, 스케일링 법칙, 오픈소스 LLM(DeepSeek, LLaMA 등)[^2_2][^2_4][^2_5]
- **특징:**
    - 수백억~수조 개의 파라미터와 방대한 데이터로 학습
    - 강력한 언어 이해/생성 능력 및 다양한 도메인(로봇, 계획, 약물발견 등) 확장
    - 오픈소스 생태계 활성화, 효율적 학습 및 추론 기술 발전[^2_3][^2_4]
    - 강화학습, 메모리 시스템, 스케일링 법칙 등 최적화 및 확장성 연구 활발[^2_4]

---

## 주요 논문 단계별 특징 요약

| 단계 | 대표 논문/기술 | 주요 특징 |
| :-- | :-- | :-- |
| SLM | n-gram, bigram, trigram | Markov 가정, 고정 컨텍스트, 차원의 저주 한계 |
| NLM | RNN, LSTM, Seq2Seq | 신경망 기반 시퀀스 처리, 장기 의존성 해결, 다양한 NLP 적용 |
| PLM | Transformer, BERT, GPT | Transformer 구조, 사전학습, 미세조정, 범용 NLP 성능 향상 |
| LLM | GPT-3, LLaMA, GPT-4, PaLM-E | 대규모 파라미터/데이터, 강력한 생성/이해, 다양한 도메인 확장 |


---

이렇게 LLM의 발전 과정은 단계별로 모델의 복잡성, 학습 데이터의 크기, 그리고 다양한 NLP 및 인공지능 분야로의 확장성에서 큰 변화를 겪어왔습니다.
각 단계의 핵심 논문과 특징을 통해 LLM의 기술적 진화를 명확히 이해할 수 있습니다[^2_1][^2_2][^2_5].
<span style="display:none">[^2_10][^2_6][^2_7][^2_8][^2_9]</span>

<div align="center">⁂</div>

[^2_1]: https://hayunjong83.tistory.com/58

[^2_2]: http://arxiv.org/pdf/2307.06435.pdf

[^2_3]: https://www.bureauworks.com/ko/blog/daegyumo-eoneo-modeli-mueosingayo

[^2_4]: https://discuss.pytorch.kr/t/2025-03-17-03-23-ml-top-ml-papers-of-the-week/6616

[^2_5]: https://velog.io/@khwee2000/논문리뷰-대규모-언어-모델LLM-관련-논문

[^2_6]: https://lgresearch.ai/blog/view?seq=473

[^2_7]: https://www.redhat.com/ko/topics/ai/what-are-large-language-models

[^2_8]: https://www.topbots.com/llm-reasoning-research-papers/

[^2_9]: https://arxiv.org/html/2501.09891v1

[^2_10]: https://github.com/Hannibal046/Awesome-LLM

