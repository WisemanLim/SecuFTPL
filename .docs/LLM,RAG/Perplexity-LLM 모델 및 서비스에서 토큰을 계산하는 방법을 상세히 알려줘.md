<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# LLM 모델 및 서비스에서 토큰을 계산하는 방법을 상세히 알려줘

LLM(대형 언어 모델)에서 토큰을 계산하는 방법은 텍스트를 모델이 이해할 수 있는 작은 단위인 '토큰'으로 분해하고, 그 토큰의 개수를 세는 과정입니다. 토큰은 일반적으로 단어, 부분 단어, 또는 심볼 단위로 나뉘며, 토큰화(Tokenization)라는 과정을 거친 후 각 토큰은 고유한 숫자 ID로 매핑되어 모델에 입력됩니다.

### 토큰화 과정과 토큰 수 계산 방법

1. **토큰이란?**
텍스트를 작은 조각으로 분해한 단위로, 단어 전체일 수도 있고, 자주 쓰이는 부분 단어(서브워드)일 수도 있습니다. 예를 들어, "dog"는 하나의 토큰이지만, "dogs"는 "dog" + "s" 처럼 2개의 토큰으로 나눠질 수도 있습니다. 토큰화는 주로 BPE(Byte Pair Encoding)나 형태소 기반의 방식 등으로 이루어집니다.
2. **토큰 리턴 및 ID 매핑**
분해된 토큰은 사전에 정의된 토큰 집합(vocabulary)에서 고유한 정수 ID와 매핑되어, 모델은 숫자로 된 이 토큰 ID 시퀀스를 입력으로 처리합니다.
3. **토큰 수 계산**
텍스트에 대해 토크나이저를 실행하여 토큰 리스트를 얻고, 그 길이를 구하면 토큰 수가 됩니다. 예를 들어, Python의 OpenAI tiktoken 라이브러리 사용 시 다음과 같은 코드로 토큰 수를 셀 수 있습니다.

```python
import tiktoken
def count_tokens(text: str, encoding_name: str) -> int:
    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(text))

num_tokens = count_tokens("Hello, world!", "cl100k_base")
print(num_tokens)  # 토큰 수 출력
```

4. **모델별 토큰화 차이**
같은 텍스트라도 사용하는 LLM 모델과 토크나이저 방식에 따라 토큰 개수가 다를 수 있습니다. 예를 들어 OpenAI의 GPT 모델들은 각각 "cl100k_base", "p50k_base" 등 서로 다른 인코딩을 사용합니다.
5. **토큰 계산의 중요성**
LLM API 호출 시 토큰 수는 비용과 성능에 영향을 미치므로, 요청 전 토큰 수를 미리 계산하여 제한 내에서 처리하는 것이 중요합니다.

### 추가 팁

- 1토큰은 평균 4글자 정도, 영어 단어의 약 3/4 단어 분량에 해당합니다.
- 토큰 개수는 입력 텍스트뿐 아니라, 대화형 모델의 경우 system/user/assistant 메시지 역할별로 추가 토큰이 붙기도 합니다.
- 토큰을 정확히 계산하려면 모델에 최적화된 토크나이저를 쓰는 것이 가장 정확합니다.

요약하면, LLM에서 토큰 계산은 텍스트를 모델 사전 기반 토큰 단위로 나누고, 그 토큰 수를 세는 과정이며, 이는 LLM 사용시 비용 관리와 효율적 데이터 처리를 위해 필수적입니다.[^1_1][^1_2][^1_3][^1_4]
<span style="display:none">[^1_10][^1_11][^1_12][^1_13][^1_14][^1_15][^1_16][^1_17][^1_18][^1_19][^1_20][^1_5][^1_6][^1_7][^1_8][^1_9]</span>

<div align="center">⁂</div>

[^1_1]: https://winder.ai/calculating-token-counts-llm-context-windows-practical-guide/

[^1_2]: https://help.openai.com/en/articles/4936856-what-are-tokens-and-how-to-count-them

[^1_3]: https://seantrott.substack.com/p/tokenization-in-large-language-models

[^1_4]: https://ai.google.dev/gemini-api/docs/tokens

[^1_5]: https://console.upstage.ai/docs/guides/counting-tokens

[^1_6]: https://skywork.ai/skypage/en/The-Ultimate-Guide-to-LLM-Token-Counters-Your-Key-to-Unlocking-AI-Efficiency-and-Cost-Control/1975590557433524224

[^1_7]: https://docs.lunar.dev/next/count-llm-tokens-flow/

[^1_8]: https://www.reddit.com/r/LocalLLaMA/comments/1chf373/find_out_how_many_tokens_something_is/

[^1_9]: https://www.youtube.com/watch?v=mpifjVPXPdE

[^1_10]: https://llmtokencounter.com

[^1_11]: https://arxiv.org/abs/2404.08335

[^1_12]: https://docs.aws.amazon.com/bedrock/latest/userguide/count-tokens.html

[^1_13]: https://milvus.io/ai-quick-reference/what-is-tokenization-in-llms

[^1_14]: https://apxml.com/courses/getting-started-with-llm-toolkit/chapter-3-context-and-token-management/counting-tokens

[^1_15]: https://direct.mit.edu/coli/article/51/3/785/128327/Tokenization-Changes-Meaning-in-Large-Language

[^1_16]: https://dev.to/ppaanngggg/how-to-count-tokens-in-frontend-for-popular-llm-models-gpt-claude-and-llama-efm

[^1_17]: https://www.reddit.com/r/LocalLLaMA/comments/1hayja1/the_necessary_and_neglected_evil_of_large/

[^1_18]: https://www.fast.ai/posts/2025-10-16-karpathy-tokenizers

[^1_19]: https://www.themoonlight.io/ko/review/tokenization-matters-degrading-large-language-models-through-challenging-their-tokenization

[^1_20]: https://www.lxt.ai/ai-glossary/tokenization-in-llms/


---

# 토큰화 알고리즘 종류와 차이점 설명해줘

LLM에서 사용하는 주요 토큰화 알고리즘과 그 차이점을 정리하면 다음과 같습니다.

### 주요 토큰화 알고리즘

1. **Byte Pair Encoding (BPE)**
    - 빈도수가 높은 문자 쌍을 반복적으로 병합하여 사전을 만들어가는 방식입니다.
    - 단어를 부분 단어(subword) 단위로 쪼개어, 희귀 단어도 효과적으로 처리할 수 있습니다.
    - GPT-2, RoBERTa 등이 사용하며, 단어 경계에 얽매이지 않고 자주 등장하는 부분 단위로 토큰화가 이뤄집니다.
    - 장점: 단어 조합이 유연하고, 희귀 단어 처리에 효과적
    - 단점: 학습 시 시간이 걸리고, 가끔 어색한 부분 토큰이 생성될 수 있음.
2. **WordPiece**
    - BPE와 유사하지만 토큰 병합 기준이 다릅니다. 빈도수가 높은 쌍을 단순 병합하는 것이 아니라, 전체 데이터에 대한 확률을 최대화하는 쌍을 병합합니다.
    - Google의 BERT, DistilBERT가 대표적으로 사용합니다.
    - 장점: 전체 데이터에 대해 최적화되어 의미론적으로 더 자연스러운 토큰 생성
    - 단점: BPE보다 구현과 학습이 복잡함.
3. **SentencePiece**
    - Google에서 만든 토크나이저로, BPE와 Unigram 모델을 모두 지원합니다.
    - 텍스트를 공백 없이 전체 문장 단위로 토큰화하며, 언어 독립적 처리에 강합니다.
    - 일본어, 한국어 같이 공백이 없는 언어에도 적합합니다.
    - 장점: 여러 언어에 적용 가능, 다양한 모델 지원, 간단한 사전 생성 및 토크나이저 학습
    - 단점: 토큰 길이가 비교적 길고, 희귀 단어 분할에 다소 비용이 들 수 있음.

### 주요 차이점 요약

| 알고리즘 | 토큰 단위 | 병합 기준 | 주요 사용 모델 | 장점 | 단점 |
| :-- | :-- | :-- | :-- | :-- | :-- |
| Byte Pair Encoding (BPE) | 부분 단어 (Subword) | 빈도수 높은 문자쌍 반복 병합 | GPT-2, RoBERTa | 희귀 단어 처리 효과적, 구현 간단 | 일부 어색한 토큰 생성 가능 |
| WordPiece | 부분 단어 (Subword) | 데이터 확률 최대화 병합 | BERT, DistilBERT | 의미론적 자연스러움, 데이터 최적화 | 학습 복잡, 느림 |
| SentencePiece | 부분 단어 및 서브워드 | BPE 또는 Unigram 모델 선택 가능 | 다국어 및 비공백 언어 모델 | 언어 독립적, 공백 없는 언어 처리 우수 | 토큰 길이 길고 학습 비용 높음 |

### 참고 사항

- 토큰화 선택은 언어 특성, 모델 요구사항, 처리 효율성 등을 고려하여 이루어집니다.
- 현대 LLM에서는 이 세 가지가 가장 널리 사용되며, 최근에는 동적 어휘 확장이나 적응형 토큰화 같은 새로운 방법도 연구되고 있습니다.

이상은 LLM에서 주로 사용되는 토큰화 알고리즘들의 기본 개념과 차이점입니다.[^2_1][^2_2][^2_3][^2_4][^2_5]
<span style="display:none">[^2_10][^2_11][^2_12][^2_13][^2_14][^2_15][^2_16][^2_17][^2_18][^2_19][^2_20][^2_6][^2_7][^2_8][^2_9]</span>

<div align="center">⁂</div>

[^2_1]: https://airbyte.com/data-engineering-resources/llm-tokenization

[^2_2]: https://arxiv.org/html/2411.17669v1

[^2_3]: https://www.eyer.ai/blog/top-10-tokenization-techniques-for-nlp/

[^2_4]: https://velog.io/@gypsi12/토크나이저-정리BPEWordPieceSentencePiece

[^2_5]: https://happygrammer.github.io/nlp/tokenizer_wordpiece_vs_sentencepiece/

[^2_6]: https://www.traceloop.com/blog/a-comprehensive-guide-to-tokenizing-text-for-llms

[^2_7]: https://www.openxcell.com/blog/llm-tokenization/

[^2_8]: https://arxiv.org/abs/2507.22920

[^2_9]: https://www.ndss-symposium.org/wp-content/uploads/bar2025-final13.pdf

[^2_10]: https://www.reddit.com/r/MachineLearning/comments/rprmq3/d_sentencepiece_wordpiece_bpe_which_tokenizer_is/

[^2_11]: https://huggingface.co/learn/llm-course/chapter6/4

[^2_12]: https://www.promptingguide.ai/research/llm-tokenization

[^2_13]: https://www.datacamp.com/blog/what-is-tokenization

[^2_14]: https://seantrott.substack.com/p/tokenization-in-large-language-models

[^2_15]: https://huggingface.co/docs/transformers/tokenizer_summary

[^2_16]: https://asidefine.tistory.com/281

[^2_17]: https://psychometrics.ai/tokenization

[^2_18]: https://ideaexchange.uakron.edu/cgi/viewcontent.cgi?article=3344\&context=honors_research_projects

[^2_19]: https://www.youtube.com/watch?v=hL4ZnAWSyuU

[^2_20]: https://aclanthology.org/2024.icnlsp-1.22/


---

# 한국어에 최적화된 토큰화 설정 추천

한국어에 최적화된 토큰화 설정은 한국어의 특성인 교착어(structure with suffixes)와 형태소 구성이 복잡한 점을 고려해 설계되어야 합니다. 주요 추천 토큰화 방법과 특성은 다음과 같습니다.

### 추천 토큰화 방법 및 설정

1. **SentencePiece 기반 한국어 토크나이저**
    - Google 등에서 많이 사용하며, 공백 없는 텍스트 처리에 강점이 있습니다.
    - 한국어 코퍼스에 특화된 SentencePiece 모델을 학습하여, 불필요 토큰 제거 및 최적의 어휘 크기(예: 30K~72K)를 설정해 효율을 높입니다.
    - 예: RedWhale, Konan-LLM 등 한국어 특화 LLM에서 이 방법을 사용하고 있습니다.
    - 장점: 언어 독립적이며, 형태소 단위와 부분 단어(subword)를 효과적으로 분할.
2. **Morphological segmentation + BPE 하이브리드**
    - 먼저 형태소 분석기로 한국어를 분리(예: Mecab-ko, Kkma) 후 BPE 인코딩을 적용하는 방식입니다.
    - KorNLI, NSMC 같은 자연어 이해 작업에서 좋은 성능을 냅니다.
    - 장점: 한국어 띄어쓰기와 어근, 조사, 어미 등을 명확히 구분하여 어휘 효율을 높임.
3. **Thunder-Tok**
    - 한국어에 특화된 새로운 토크나이저로, 일반 BPE 대비 약 10% 적은 토큰 수로 같은 텍스트를 표현합니다.
    - 형태소 수준 중심으로 토큰을 구성해 Llama 기반 한국어 모델에 활용되고 있습니다.
    - 장점: 토큰 수 절약 및 처리 효율 향상.
4. **Unigram 기반 SentencePiece 변형**
    - Llama 한국어 확장 버전에서 활용되는 방식으로, 로그 확률 기반 최적 경로를 태깅하며, 한국어에 적합한 토큰 어휘를 추가하여 성능과 효율성 균형을 맞춤.

### 한국어 토크나이저 설정 추천 요약

| 방법 | 특징 및 장점 | 활용 예시 프로젝트/모델 |
| :-- | :-- | :-- |
| SentencePiece (한국어 특화) | 공백 무관, 형태소 및 부분 단어 효과적 처리, 확장 가능 | RedWhale, Konan-LLM |
| 형태소 분석 + BPE 하이브리드 | 형태소 단위 분리 후 BPE, 자연어 이해 과제에 강점 | KorNLI, NSMC 자연어처리 태스크 |
| Thunder-Tok | 한국어 모폴로지 기반 특화, 토큰 수 절감 효과 | Llama-Thunder-LLM |
| Unigram SentencePiece 변형 | 확률 기반 최적 경로 선택, 한국어 토큰 확장 | Llama 한국어 확장 모델 |

### 추가 팁

- 한국어는 조사, 어미 등 문법적 변화가 많아 형태소 단위 분석 병행하는 하이브리드 토큰화가 유리합니다.
- 어휘 크기는 30,000~70,000 범위에서 언어 특성에 맞게 조절하는 게 좋습니다.
- 불필요 토큰 제거 및 고빈도 토큰 위주 선택으로 토큰 효율을 높이는 전략이 필요합니다.

따라서, 한국어 대형 언어 모델이나 서비스에서는 한국어 형태소 분석을 포함하거나 한국어 코퍼스에 맞춰 학습시킨 SentencePiece, Thunder-Tok 같은 특화 토크나이저를 활용하는 것이 권장됩니다.[^3_1][^3_2][^3_3][^3_4][^3_5]
<span style="display:none">[^3_10][^3_11][^3_12][^3_13][^3_14][^3_15][^3_16][^3_17][^3_18][^3_19][^3_20][^3_6][^3_7][^3_8][^3_9]</span>

<div align="center">⁂</div>

[^3_1]: https://arxiv.org/html/2408.11294v1

[^3_2]: https://champ.snu.ac.kr/toolkits-tok.html

[^3_3]: https://arxiv.org/html/2506.21595v1

[^3_4]: https://arxiv.org/abs/2010.02534

[^3_5]: https://aclanthology.org/2020.aacl-main.17/

[^3_6]: https://www.sciencedirect.com/science/article/pii/S0952197625016884

[^3_7]: https://huggingface.co/mykor/Konan-LLM-OND-gguf

[^3_8]: https://www.themoonlight.io/en/review/how-does-a-language-specific-tokenizer-affect-llms

[^3_9]: https://community.openai.com/t/need-more-efficient-tokenizer-for-korean/286682

[^3_10]: https://arxiv.org/abs/2502.12560

[^3_11]: https://www.imranabdullah.com/2021-12-15/Korean-text-tokenization-using-PyKoTokenizer-a-model-based-approach

[^3_12]: https://tonybaloney.github.io/posts/cjk-chinese-japanese-korean-llm-ai-best-practices.html

[^3_13]: https://clova.ai/en/tech-blog/introducing-hyperclova-x-our-state-of-the-art-ai-models-optimized-for-the-korean-language

[^3_14]: https://clova.ai/en/tech-blog/inside-llm-serving-1-the-journey-of-a-token

[^3_15]: https://www.koreascience.kr/article/CFKO202404272002505.view?orgId=anpor\&hide=breadcrumb%2Cjournalinfo

[^3_16]: https://www.rws.com/language-weaver/blog/issue-132-tokenization-strategies-for-korean-mt-tasks/

[^3_17]: https://developers.hyundaimotorgroup.com/blog/430

[^3_18]: https://huggingface.co/yanolja/YanoljaNEXT-EEVE-10.8B

[^3_19]: https://nlp2024.jeju.ai/en/week02/session3.html

[^3_20]: https://aclanthology.org/2020.aacl-main.17.pdf


---

# Claud code, Gemini 등의 토큰 수 비교해줘. Input, output, total 등

Claude와 Gemini LLM 모델의 토큰 수 제한 및 입력, 출력 토큰 사용량에 대해 비교 정리하면 다음과 같습니다.

### Claude 토큰 수 및 사용량

- 토크나이저: Anthropic 고유 토크나이저 사용, 토큰은 약 3.5 영어 문자 정도에 대응.
- 입력 토큰 수: 모델에 따라 다르지만 일반적으로 수만 토큰 단위 (예: Claude 3 모델 100k 토큰 내외).
- 출력 토큰 수: 보통 입력보다 적거나 비슷한 수준으로 제한됨.
- 토큰 합계: 요청 시 입력 토큰수 + 출력 토큰수 합산하여 청구.
- 사례: 입력 1000토큰, 출력 2000토큰 시 총 3000토큰 사용으로 계산됨.
- 토큰 수 제한은 모델별로 다르나, 과거 Claude Code의 경우 수천에서 수만 토큰 입력 가능, 출력 토큰은 보통 몇 천 단위로 제한됨.


### Gemini 토큰 수 및 사용량

- 토크나이저: 공개된 상세 토크나이저는 아직 제한적이나, GPT-tiktoken과 유사 추정.
- 입력 토큰 제한: Gemini 1.5-flash 기준 약 1,000,000 토큰 (1백만 토큰)까지 입력 허용, 매우 큰 컨텍스트 윈도우 제공.
- 출력 토큰 제한: 기본적으로 몇 천 단위(예: 8,000 토큰) 출력 제한 존재.
- 토큰 합계: 입력과 출력 토큰 합산하여 계산하나, 입력 토큰 수 제한이 매우 큼.
- 대화 상태를 유지하며 이전 대화 내용 재입력 시 토큰 수가 누적되어 계산됨.


### 비교 요약

| 항목 | Claude | Gemini |
| :-- | :-- | :-- |
| 입력 토큰 제한 | 보통 수만 토큰 (예: 수십만 미만) | 약 1,000,000 토큰 (1백만 한도) |
| 출력 토큰 제한 | 수 천~수만 토큰 이내 | 약 8,000 토큰 기본 출력 제한 |
| 토큰 합계 계산 | 입력 + 출력 토큰 합산 | 입력 + 출력 토큰 합산 |
| 토큰 단위 특징 | 약 3.5 문자 대응 | GPT-tiktoken 유사, 문자/단어 병합 |
| 특징 | 코드, 복잡도 높은 작업에 적합 | 대용량 컨텍스트 처리에 우수 |

요약하면, Gemini가 최대 입력 토큰수가 압도적으로 크며 특히 수십만~100만 토큰 단위의 긴 컨텍스트 윈도우가 강점입니다. Claude는 상대적으로 입력 토큰 제한은 작지만 실제 출력 토큰과 문맥 유지, 복잡한 작업에 최적화되어 있습니다. 토큰 수는 입력과 출력 합산 기준이며, 호출 API나 서비스마다 실제 제한과 비용 정책이 다를 수 있습니다.[^4_1][^4_2][^4_3][^4_4][^4_5][^4_6]
<span style="display:none">[^4_10][^4_11][^4_12][^4_13][^4_14][^4_15][^4_16][^4_17][^4_18][^4_19][^4_20][^4_7][^4_8][^4_9]</span>

<div align="center">⁂</div>

[^4_1]: https://platform.claude.com/docs/en/build-with-claude/token-counting

[^4_2]: https://www.youtube.com/watch?v=EssztxE9P28

[^4_3]: https://github.com/google-gemini/gemini-cli/issues/2479

[^4_4]: https://www.propelcode.ai/blog/token-counting-tiktoken-anthropic-gemini-guide-2025

[^4_5]: https://ai.google.dev/gemini-api/docs/tokens

[^4_6]: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/2-5-pro

[^4_7]: https://www.reddit.com/r/ClaudeAI/comments/1bgg5v0/how_do_you_countestimate_token_inputoutputs_with/

[^4_8]: https://preslav.me/2025/08/04/put-claude-code-token-usage-macos-toolbar/

[^4_9]: https://github.com/anthropics/claude-code/issues/11563

[^4_10]: https://www.tribe.ai/applied-ai/a-quickstart-for-measuring-the-return-on-your-claude-code-investment

[^4_11]: https://github.com/yamadashy/repomix/issues/476

[^4_12]: https://ccusage.com/guide/monthly-reports

[^4_13]: https://gptforwork.com/tools/tokenizer

[^4_14]: https://northflank.com/blog/claude-rate-limits-claude-code-pricing-cost

[^4_15]: https://docs.cloud.google.com/vertex-ai/generative-ai/pricing

[^4_16]: https://www.reddit.com/r/ClaudeAI/comments/1jlu8ii/is_gemini_25_with_a_1m_token_limit_just_insane/

[^4_17]: https://docs.aws.amazon.com/bedrock/latest/userguide/count-tokens.html

[^4_18]: https://firebase.google.com/docs/ai-logic/count-tokens

[^4_19]: https://www.datastudios.org/post/google-gemini-vs-anthropic-claude-full-report-and-comparison-august-2025-updated

[^4_20]: https://www.arsturn.com/blog/mastering-claudes-token-limits-a-beginners-guide


---

# 각 모델별 동일한 한국어 문장 샘플로 토큰 수 측정해줘

한국어 문장에 대해 Claude와 Gemini 모델 토크나이저를 직접 실행하여 토큰 수를 비교하려 했으나, 현재 환경에서 Gemini의 정확한 토크나이저가 공개되어 있지 않고 실행 시간 제한 문제로 직접 측정은 어려웠습니다.

대신 일반적으로 Claude는 GPT-2 계열의 BPE 토크나이저와 유사하며, Gemini는 SentencePiece 또는 GPT-tiktoken과 유사한 방식으로 토큰화를 하는 것으로 알려져 있습니다. 예를 들어,

- GPT-2 토크나이저는 "안녕하세요, 오늘은 대형 언어 모델 토큰화를 비교해보겠습니다." 문장에 대해 약 17~20 토큰 정도가 나올 수 있습니다.
- SentencePiece 계열 토크나이저(예: KoBERT)는 같은 문장에 대해 보통 더 세밀한 형태소 단위 분할로 25~30 토큰 수준이 될 수 있습니다.

결론적으로 Claude는 비교적 큰 단위의 토큰화를 하는 반면, Gemini는 한국어에 최적화된 세밀한 토큰화를 적용해 토큰 수가 더 많을 수 있으니 토큰 사용량 산정 시 이 점 참고하는 것이 좋습니다.

실제로 동일한 문장에 대해 정확한 토큰수를 수치로 비교하려면 해당 서비스 API 호출을 통한 토큰 계산이나 공개된 토크나이저 라이브러리 활용이 필요합니다.[^5_1][^5_2][^5_3]

<div align="center">⁂</div>

[^5_1]: https://platform.claude.com/docs/en/build-with-claude/token-counting

[^5_2]: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/2-5-pro

[^5_3]: https://arxiv.org/html/2506.21595v1


---

# Perplexity, chatgpt 등의 공개된 모델의 토큰 사용량 계산 방법 및 토큰수를 비교해 줘

Perplexity와 ChatGPT(특히 OpenAI GPT 시리즈) 모델의 토큰 사용량 계산 방법과 토큰 수 비교는 다음과 같습니다.

### 토큰 사용량 계산 방법

#### ChatGPT (OpenAI GPT 시리즈)

- 토큰 세기는 OpenAI의 tiktoken 라이브러리로 계산하며, 입력(prompt)과 출력(response) 모두 토큰 단위로 셉니다.
- 메시지 하나가 여러 필드로 구성된 대화형 API 특성상, 시스템 메시지, 사용자 메시지, 어시스턴트 메시지 각각에 3~5개 추가 토큰이 붙을 수 있음.
- 총 토큰 수 = 입력 토큰 수 + 출력 토큰 수 + 메시지 메타 정보 토큰 수
- 예: Python tiktoken 라이브러리로 토큰 계산 시, 각 텍스트를 인코딩하여 토큰 길이를 구하는 방식으로 정확한 계산이 가능함.


#### Perplexity AI

- Perplexity는 약 1,000 tokens ≈ 750 단어(영어 기준)로 계산하며, 한국어는 조금 다를 수 있으나 비슷한 수준으로 봅니다.
- 토큰 제한은 최대 8,000토큰(입력 + 출력 + 시스템/툴 텍스트 포함)이며, 제한을 초과하면 오래된 내용을 줄이거나 응답 크기를 제한합니다.
- Perplexity는 입력과 출력 토큰 모두 합산해서 처리하며, 웹 검색 등 배경 데이터가 추가되면 토큰 카운트에 포함됩니다.


### 토큰 수 비교

| 측면 | ChatGPT (OpenAI GPT) | Perplexity AI |
| :-- | :-- | :-- |
| 토큰 단위 | English 기준 1토큰 ≈ 4글자 | 유사, 영어 기준 1,000토큰 ≈ 750단어 |
| 최대 컨텍스트 윈도우 | 모델 버전 따라 다름 (e.g., GPT-4: 8,192~32,768 토큰) | 최대 8,000 토큰 (입력 + 출력 + 시스템 포함) |
| 토큰 계산 포함 대상 | 모든 메시지와 메타데이터 포함 | 입력, 출력, 시스템 및 기타 텍스트 포함 |
| 계산 방법 | tiktoken 기반, API에서 제공하는 계산법 사용 | 자체 토크나이저 기반, API에서 토큰 수 반환 |
| 비용 산정 기준 | 입력 + 출력 토큰 합산 | 입력 + 출력 + 검색 및 시스템 토큰 합산 |

### 요약

- 두 모델 모두 입력과 출력 토큰 수를 합산하여 토큰 사용량을 계산하지만, ChatGPT는 메시지 형식에 따라 추가 토큰이 붙고, Perplexity는 검색 및 시스템 텍스트 토큰도 포함한다는 점이 다릅니다.
- 컨텍스트 윈도우 크기는 ChatGPT 모델의 최신 버전이 더 넓지만, Perplexity는 실시간 정보 검색과 결합해 토큰 사용을 관리합니다.
- 실제 토큰 수 계산은 공식 토크나이저 라이브러리(예: OpenAI tiktoken 또는 Perplexity 자체 토크나이저)를 활용하는 것이 정확합니다.

한국어의 경우 문자당 토큰 수는 영어보다 약간 더 많을 수 있으므로, 동일 텍스트 기준으로는 약간의 차이가 발생합니다.[^6_1][^6_2][^6_3][^6_4][^6_5][^6_6]
<span style="display:none">[^6_10][^6_11][^6_12][^6_13][^6_14][^6_15][^6_16][^6_17][^6_18][^6_19][^6_20][^6_7][^6_8][^6_9]</span>

<div align="center">⁂</div>

[^6_1]: https://docs.perplexity.ai/getting-started/pricing

[^6_2]: https://www.perplexity.ai/help-center/en/articles/10354924-about-tokens

[^6_3]: https://visionvix.com/perplexity-vs-chatgpt-comparison-and-reviews/

[^6_4]: https://www.datastudios.org/post/perplexity-ai-context-window-token-limits-memory-policy-and-2025-rules

[^6_5]: https://stackoverflow.com/questions/77168202/calculating-total-tokens-for-api-request-to-chatgpt-including-functions

[^6_6]: https://platform.openai.com/tokenizer

[^6_7]: https://pricepertoken.com/token-counter/provider/perplexity

[^6_8]: https://www.helicone.ai/llm-cost/provider/perplexity/model/sonar

[^6_9]: https://stackoverflow.com/questions/77433100/how-to-get-perplexity-per-token-rather-than-average-perplexity

[^6_10]: https://github.com/liuliuOD/ChatGPT-Token-Usage-Pre-Calculator

[^6_11]: https://www.reddit.com/r/perplexity_ai/comments/1mzb2sz/perplexity_vs_chatgpt/

[^6_12]: https://www.reddit.com/r/perplexity_ai/comments/1bneo5m/default_api_token_usageprice/

[^6_13]: https://joymaster.tistory.com/entry/ChatGPT-Python-토큰Token-계산하기

[^6_14]: https://aloa.co/ai/comparisons/llm-comparison/chatgpt-vs-perplexity

[^6_15]: https://github.com/EleutherAI/lm-evaluation-harness/issues/2170

[^6_16]: https://help.openai.com/en/articles/4936856-what-are-tokens-and-how-to-count-them

[^6_17]: https://www.datastudios.org/post/chatgpt-vs-perplexity-ai-full-report-and-comparison-comparison-of-features-capabilities-pricing

[^6_18]: https://huggingface.co/docs/transformers/perplexity

[^6_19]: https://explodingtopics.com/blog/perplexity-ai-vs-chatgpt

[^6_20]: https://apxml.com/courses/how-to-build-a-large-language-model/chapter-21-intrinsic-evaluation-metrics/perplexity-definition-calculation

