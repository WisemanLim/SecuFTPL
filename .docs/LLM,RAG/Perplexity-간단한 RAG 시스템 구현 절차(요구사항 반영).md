<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

### 간단한 RAG 시스템 구현 절차 (요구사항 반영)

아래는 PDF 업로드부터 LLM 기반 답변까지 한 번에 구현 가능한 RAG (Retrieval-Augmented Generation) 시스템의 구조와 주요 구현 흐름입니다.

***

#### 1. PDF 파일 Drag \& Drop 업로드

- 웹 프론트엔드(React, Vue, Svelte 등)에서 사용자가 PDF 파일을 drag \& drop으로 업로드할 수 있는 파일 입력 UI를 만듭니다.
- 업로드된 파일은 서버로 전달하거나, 프론트엔드에서 바로 텍스트로 변환(브라우저 환경 한정)을 시도할 수 있습니다.

***

#### 2. 업로드된 파일 텍스트 추출 및 청킹

- **Python 백엔드**에서는 일반적으로 `PyPDF2`, `PyMuPDF(fitz)`, 또는 `pdfplumber`와 같은 라이브러리로 PDF의 텍스트를 추출합니다.[^1_1][^1_2]
    - 추출 예시(Python):

```python
from PyPDF2 import PdfReader
reader = PdfReader("example.pdf")
all_text = ""
for page in reader.pages:
    all_text += page.extract_text() + "\n"
```

- **Chunking(청킹):**
    - 보통 300~1,000단어씩 나누는데, 단순 split 또는 의미 단위(문단, 문장 등)로 나누는 방법이 쓰입니다.
    - 예시(Python):

```python
def chunk_text(text, chunk_size=500):
    words = text.split()
    return [' '.join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]
```


***

#### 3. 청킹 완료 후 질문 입력 UI 제공

- 프론트엔드에서 “질문을 입력하세요”와 같은 input 필드를 화면에 표시합니다.
- 시스템 뒷단에서는 각 청크에 대해 embedding 생성(예: OpenAI, Sentence Transformers), embedding을 벡터DB에 저장합니다.

***

#### 4. 사용자 질문 입력 → LLM 기반 답변

1. **질문 벡터화:**
사용자의 질문을 embedding으로 변환합니다.
2. **유사 청크 검색:**
벡터DB(예: FAISS, Qdrant, Pinecone 등)에서 가장 연관도 높은 청크 3~5개를 추출합니다.
3. **LLM 질의:**
선택된 텍스트 청크와 사용자의 질문을 함께 LLM(GPT, Llama2/3 등)에 넣고 답변을 생성하여 반환합니다.

***

### 전체 아키텍처 요약

| 단계 | 핵심 함수/기술 | 간단 설명 |
| :-- | :-- | :-- |
| PDF 업로드 | 웹 UI | drag \& drop으로 파일 선택 |
| 텍스트 추출 | PyPDF2, PyMuPDF, API 등 | 파일→텍스트 변환 |
| 청킹 | Python, Node 등 직접구현 | 500~1000단어 단위 분할 |
| 임베딩 | OpenAI/SBert 등 | 각 청크를 벡터화 |
| 검색 | FAISS, Qdrant, Pinecone | 질문 임베딩과 유사한 청크 검색 |
| LLM 답변 | LLM API, 오픈소스 등 | 청크+질문 입력 → context-aware 답변 생성 |


***

### 참고

- 실제 구현 예제, 프레임워크, 라이브러리, 설정 방법 등은 여러 튜토리얼에서 단계별로 다룹니다.[^1_3][^1_4][^1_5]
- 간단한 end-to-end 예시와 더 상세한 구현 방법은 여기에서 확인 가능합니다:
    - Hugging Face 예시[^1_6]
    - DZone 실습 튜토리얼[^1_5]
    - RAG와 PDF 작업 개념[^1_2][^1_3][^1_1]

***

이 절차에 따라, 적절한 프론트엔드(파일 업로드 \& 질문 입력), PDF 텍스트 추출 및 청킹, embedding/검색, LLM 답변 생성까지 시스템을 쉽게 만들 수 있습니다.
<span style="display:none">[^1_10][^1_11][^1_12][^1_13][^1_14][^1_15][^1_16][^1_17][^1_18][^1_19][^1_20][^1_21][^1_22][^1_23][^1_24][^1_25][^1_26][^1_27][^1_28][^1_29][^1_30][^1_31][^1_32][^1_33][^1_34][^1_7][^1_8][^1_9]</span>

<div align="center">⁂</div>

[^1_1]: https://www.metriccoders.com/post/a-guide-to-pdf-extraction-libraries-in-python

[^1_2]: https://unstract.com/blog/evaluating-python-pdf-to-text-libraries/

[^1_3]: https://djangostars.com/blog/rag-question-answering-with-python/

[^1_4]: https://python.plainenglish.io/chatting-with-pdfs-building-a-simple-rag-system-6d3617ae77d3

[^1_5]: https://dzone.com/articles/rag-model-for-pdf-content-extraction-and-query-answering

[^1_6]: https://huggingface.co/blog/ngxson/make-your-own-rag

[^1_7]: https://cookbook.openai.com/examples/file_search_responses

[^1_8]: https://blog.sionic.ai/naive-rag

[^1_9]: https://community.openai.com/t/what-is-the-best-way-to-chunk-a-pdf-file-for-rag-in-a-smart-way-that-preserves-the-meaning-during-retrieval/654863

[^1_10]: https://www.reddit.com/r/LangChain/comments/1hl94lj/best_way_for_image_chunking_in_ragbased_pdf/

[^1_11]: https://www.edenai.co/post/use-rag-to-chat-with-pdfs-build-your-own-pdf-chabot-with-llms

[^1_12]: https://pypdf.readthedocs.io/en/stable/user/extract-text.html

[^1_13]: https://humanloop.com/blog/rag-architectures

[^1_14]: https://www.multimodal.dev/post/how-to-chunk-documents-for-rag

[^1_15]: https://www.thedataschool.com/salome-grasland/converting-a-pdf-to-text-file-using-python/

[^1_16]: https://www.uncu.me/articles/building-pdf-rag-system-practical-guide

[^1_17]: https://www.geeksforgeeks.org/python/extract-text-from-pdf-file-using-python/

[^1_18]: https://www.youtube.com/watch?v=2TJxpyO3ei4

[^1_19]: https://wooiljeong.github.io/python/pdf-to-text/

[^1_20]: https://python.langchain.com/docs/tutorials/rag/

[^1_21]: https://www.reddit.com/r/LangChain/comments/1e7cntq/whats_the_best_python_library_for_extracting_text/

[^1_22]: https://www.chatbase.co/blog/rag-from-scratch

[^1_23]: https://stackoverflow.com/questions/34837707/how-to-extract-text-from-a-pdf-file-via-python

[^1_24]: https://docs.mistral.ai/guides/rag/

[^1_25]: https://weclouddata.com/blog/building-a-question-answering-system-using-rag/

[^1_26]: https://arxiv.org/html/2410.15944v1

[^1_27]: https://murf.ai/blog/build-pdf-rag-based-app-with-langchain

[^1_28]: https://dspy.ai/tutorials/rag/

[^1_29]: https://www.nutrient.io/blog/top-10-ways-to-generate-pdfs-in-python/

[^1_30]: https://galileo.ai/blog/mastering-rag-advanced-chunking-techniques-for-llm-applications

[^1_31]: https://www.youtube.com/watch?v=Ddk8bA6OWjQ

[^1_32]: https://www.reddit.com/r/LocalLLaMA/comments/1dpb9ow/how_we_chunk_turning_pdfs_into_hierarchical/

[^1_33]: https://community.openai.com/t/best-way-to-interact-with-pdf-2025/1098423

[^1_34]: https://www.mongodb.com/developer/products/atlas/choosing-chunking-strategy-rag/


---

# python의 streamlit을 이용하여 코드를 구현해 주세요.

좋습니다.
이전 대화에서 설명드린 **간단한 RAG (Retrieval-Augmented Generation) 시스템**을 이번에는 **Python + Streamlit**으로 실제 코드 예시 형태로 구현해드리겠습니다.

아래 예시는 주요 4단계를 모두 포함합니다.

- PDF Drag \& Drop 업로드
- 텍스트 추출 \& 청킹
- 질문 입력
- LLM 기반 답변 생성

***

## **전체 코드 예제 (Streamlit)**

```python
# app.py
import streamlit as st
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer
import faiss
import openai

# 🔹 환경 변수 또는 직접 API 키 입력
openai.api_key = "YOUR_OPENAI_API_KEY"  # 안전하게 환경변수로 관리 권장

# 임베딩 모델 (로컬) - 속도 빠름
embedder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# FAISS index (in-memory)
dimension = 384  # all-MiniLM-L6-v2 의 차원 수
index = faiss.IndexFlatL2(dimension)
document_chunks = []  # 청크 텍스트 저장 (retrieval 시 원문 반환)

# ---------------------
# 유틸 함수
# ---------------------
def extract_text_from_pdf(uploaded_file):
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def chunk_text(text, chunk_size=500):
    words = text.split()
    return [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]

def build_vector_store(chunks):
    global index, document_chunks
    document_chunks = chunks
    embeddings = embedder.encode(chunks)
    index.add(embeddings)

def retrieve(query, top_k=3):
    query_emb = embedder.encode([query])
    D, I = index.search(query_emb, top_k)
    return [document_chunks[i] for i in I[0]]

def generate_answer(context_chunks, question):
    context_text = "\n\n".join(context_chunks)
    prompt = f"""다음 문서 내용 일부를 참고하여 질문에 답변하세요.

문서 내용:
{context_text}

질문: {question}

답변:"""

    completion = openai.ChatCompletion.create(
        model="gpt-4o-mini",  # 필요 시 다른 모델 사용 가능
        messages=[
            {"role": "system", "content": "당신은 문서 내용을 기반으로 답변하는 AI입니다."},
            {"role": "user", "content": prompt}
        ]
    )
    return completion.choices[0].message.content.strip()

# ---------------------
# Streamlit UI
# ---------------------
st.set_page_config(page_title="간단한 RAG 시스템", layout="wide")
st.title("📄 PDF 기반 RAG QA")

uploaded_file = st.file_uploader("PDF 파일을 드래그 앤 드롭 하세요", type=["pdf"])

if uploaded_file is not None:
    with st.spinner("PDF 텍스트 추출 중..."):
        text = extract_text_from_pdf(uploaded_file)
        chunks = chunk_text(text, chunk_size=300)
        build_vector_store(chunks)
    st.success("✅ PDF 업로드 및 청킹 완료!")

    question = st.text_input("질문을 입력하세요")
    if question:
        with st.spinner("답변 생성 중..."):
            retrieved_chunks = retrieve(question)
            answer = generate_answer(retrieved_chunks, question)

        st.subheader("💡 답변:")
        st.write(answer)

        with st.expander("🔍 참조한 문서 내용 보기"):
            for i, chunk in enumerate(retrieved_chunks, 1):
                st.markdown(f"**참조 청크 {i}:**\n{chunk}")
```


***

## **동작 흐름**

1. **PDF 업로드**
    - `st.file_uploader`로 Drag \& Drop 기능 제공
    - `PyPDF2`로 텍스트 추출
2. **청킹**
    - `chunk_text` 함수로 일정 단위 분리 (여기선 300 단어)
3. **임베딩 + 벡터DB 저장**
    - `SentenceTransformer(all-MiniLM-L6-v2)`로 임베딩 생성
    - `FAISS` 인메모리 인덱스에 저장
4. **질문 처리**
    - 질문 임베딩 → FAISS 검색 → 가장 유사한 청크 반환
5. **LLM 호출**
    - context + 질문을 `OpenAI ChatCompletion` API에 전달
    - 문서 기반으로 답변 생성

***

## **설치 방법**

```bash
pip install streamlit PyPDF2 sentence-transformers faiss-cpu openai
```


## **실행 명령**

```bash
streamlit run app.py
```


***

💡 이 예시는 **로컬에서 간단하게 구현하는 RAG** 구조이고,
Pinecone, Qdrant 같은 외부 벡터DB로 쉽게 확장 가능하며,
OpenAI 대신 Llama3, Mistral 등 오픈소스 LLM도 적용 가능합니다.

***

원하시면 제가 이 예시를 **Pinecone + LangChain 버전**으로 확장해서 더 강력한 RAG 시스템 예제를 만들어 드릴 수도 있습니다.
그렇게 진행할까요?

---

# 예. 진행해 주세요.

좋습니다 👍
이전에 만든 **Streamlit + 단일 PDF + 로컬 FAISS** 버전을 이번에는 **Pinecone + LangChain**을 사용해서 확장한 **더 강력한 RAG 시스템**으로 구현해 드리겠습니다.

이 버전은 다음과 같이 개선됩니다.

- **Pinecone**: 대규모 문서 저장 가능(클라우드 호스팅)
- **LangChain**: PDF 로딩, 청킹, 임베딩, 검색, LLM 체인까지 간소화
- 여러 PDF 파일도 업로드 가능
- 확장성과 유지보수 용이

***

## 1. 사전 준비

1. **Pinecone 계정 생성 후 API 키 발급**
2. **OpenAI API 키 준비**
3. `.env` 파일에 아래 내용 저장:
```env
OPENAI_API_KEY=your_openai_api_key
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENVIRONMENT=your_pinecone_environment  # 예: gcp-starter
PINECONE_INDEX_NAME=pdf-rag
```


***

## 2. 설치

```bash
pip install streamlit langchain langchain-community langchain-openai pinecone-client PyPDF2 python-dotenv
```


***

## 3. Streamlit + Pinecone + LangChain 코드

```python
# app_pinecone.py
import streamlit as st
import os
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Pinecone as PineconeVectorStore
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from pinecone import Pinecone, ServerlessSpec
from langchain.chains import RetrievalQA

# ---------------------
# 환경 변수 로드
# ---------------------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

# ---------------------
# Pinecone 초기화
# ---------------------
pc = Pinecone(api_key=PINECONE_API_KEY)

if PINECONE_INDEX_NAME not in [idx["name"] for idx in pc.list_indexes()]:
    pc.create_index(
        name=PINECONE_INDEX_NAME,
        dimension=1536,  # OpenAI embedding 차원
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )
index = pc.Index(PINECONE_INDEX_NAME)

# ---------------------
# PDF 처리 함수
# ---------------------
def extract_text_from_pdfs(uploaded_files):
    text = ""
    for uploaded_file in uploaded_files:
        pdf = PdfReader(uploaded_file)
        for page in pdf.pages:
            content = page.extract_text()
            if content:
                text += content + "\n"
    return text

def chunk_text(text, chunk_size=1000, chunk_overlap=200):
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.split_text(text)

def build_vector_store(chunks):
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    vector_store = PineconeVectorStore.from_texts(chunks, embedding=embeddings, index_name=PINECONE_INDEX_NAME)
    return vector_store

# ---------------------
# Streamlit UI
# ---------------------
st.set_page_config(page_title="Pinecone 기반 PDF QA", layout="wide")
st.title("📄 Pinecone + LangChain PDF RAG 시스템")

uploaded_files = st.file_uploader("PDF 파일 업로드 (여러 개 가능)", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    with st.spinner("PDF에서 텍스트 추출 중..."):
        text = extract_text_from_pdfs(uploaded_files)
        chunks = chunk_text(text)
        build_vector_store(chunks)
    st.success("✅ Pinecone에 문서 저장 완료!")

    question = st.text_input("질문을 입력하세요")
    if question:
        with st.spinner("답변 생성 중..."):
            embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
            vector_store = PineconeVectorStore(index, embeddings.embed_query, "text")
            retriever = vector_store.as_retriever(search_kwargs={"k": 3})
            llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
            qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever, return_source_documents=True)
            result = qa_chain({"query": question})

        st.subheader("💡 답변")
        st.write(result["result"])

        with st.expander("🔍 참조한 문서 내용 보기"):
            for i, doc in enumerate(result["source_documents"], 1):
                st.markdown(f"**참조 청크 {i}:**\n{doc.page_content}")
```


***

## 4. 실행

```bash
streamlit run app_pinecone.py
```


***

## 5. 작동 방식

1. **PDF 업로드**
    - 여러 PDF를 지원, 모든 페이지 텍스트 병합
2. **청킹**
    - LangChain의 `RecursiveCharacterTextSplitter`로 의미 단위 나눔
3. **Pinecone 저장**
    - OpenAI Embeddings(`text-embedding-3-small`)로 변환 후 Pinecone Index 저장
4. **질문 입력**
    - Pinecone에서 유사도 기반 검색
5. **LLM 답변**
    - GPT-4o-mini 모델이 문서 기반으로 답변 생성

***

💡 이 구조를 사용하면

- 문서를 한 번 임베딩 후 Pinecone에 저장 → 재사용 가능
- 여러 사용자/세션이 같은 인덱스를 공유 가능
- PDF 외에 Word, 텍스트 파일 등으로 확장 용이

***

원하시면 제가 이 버전을 **대규모 PDF 폴더 자동 처리 + 메타데이터 기반 필터링 기능**까지 추가해서 드릴 수 있습니다.
그렇게 확장할까요?

---

### 대용량 PDF 폴더 자동 처리 + 메타데이터 기반 필터링 확장 예시

아래는 Streamlit + Pinecone + LangChain 환경에서 **폴더 단위 PDF 자동 ingestion, 메타데이터 추출·저장, 검색 시 메타데이터 필터링**까지 수행하는 실전 코드 예시입니다.
이 예시는 대량의 PDF 처리, 원본 파일 및 chunk ID 기준의 검색, 파일명이나 기타 메타데이터별로 RAG 질의가 가능합니다.

***

#### 주요 확장 포인트

- **여러 PDF 파일 또는 폴더 단위 업로드** 가능 (Streamlit)
- **PDF별 chunk 생성** 시, 각 chunk에
    - 원본 파일명 (`source`)
    - 청크 인덱스 (`chunk`)
    - 등 메타데이터를 추가하여 저장
- **Pinecone**에 벡터 + 메타데이터 함께 저장,
LangChain Retriever에서 메타데이터 조건(`filter`)으로 빠른 필터링/검색 지원
- **질문 시** 옵션값(예시: `source:example.pdf`)으로 특정 파일에 대한 검색만 제한 가능

***

### 전체 Python 코드 예시

```python
import streamlit as st
import os
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Pinecone as PineconeVectorStore
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from pinecone import Pinecone, ServerlessSpec
from langchain.chains import RetrievalQA
from langchain.schema import Document

# 환경변수 로드
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

# Pinecone 초기화
pc = Pinecone(api_key=PINECONE_API_KEY)
if PINECONE_INDEX_NAME not in [idx["name"] for idx in pc.list_indexes()]:
    pc.create_index(
        name=PINECONE_INDEX_NAME,
        dimension=1536,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )
index = pc.Index(PINECONE_INDEX_NAME)

# PDF 텍스트 + 메타데이터 추출
def load_and_split_pdfs(files):
    all_docs = []
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    for uploaded_file in files:
        pdf = PdfReader(uploaded_file)
        raw_text = ""
        for page in pdf.pages:
            page_content = page.extract_text()
            if page_content:
                raw_text += page_content + "\n"
        chunks = text_splitter.split_text(raw_text)
        for i, chunk in enumerate(chunks):
            doc = Document(
                page_content=chunk,
                metadata={"source": uploaded_file.name, "chunk": i}
            )
            all_docs.append(doc)
    return all_docs

# 벡터스토어 구축
def build_vector_store_with_metadata(docs):
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    vector_store = PineconeVectorStore.from_documents(
        docs,
        embedding=embeddings,
        index_name=PINECONE_INDEX_NAME
    )
    return vector_store

# Streamlit UI
st.set_page_config(page_title="Advanced PDF RAG with Metadata", layout="wide")
st.title("📁 대용량 PDF 폴더 자동 처리 + 메타데이터 기반 필터링 RAG 시스템")

uploaded_files = st.file_uploader("여러 PDF 파일 또는 폴더 업로드", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    with st.spinner("PDF에서 텍스트 추출 및 청킹 중..."):
        docs = load_and_split_pdfs(uploaded_files)
        vector_store = build_vector_store_with_metadata(docs)
    st.success("✅ PDF 로딩 및 임베딩 완료 (메타데이터 포함)!")

    st.info("메타데이터에 따른 필터링을 사용할 수 있습니다. 예: source:filename.pdf")

    question = st.text_input("질문을 입력하세요")

    metadata_filter_input = st.text_input("메타데이터 필터 (옵션, 예: source:yourfile.pdf)")
    metadata_filter = None
    if metadata_filter_input:
        try:
            key, value = metadata_filter_input.split(":", 1)
            metadata_filter = {key.strip(): value.strip()}
        except ValueError:
            st.error("메타데이터 필터 형식은 'key:value' 이어야 합니다.")

    if question:
        with st.spinner("답변 생성 중..."):
            retriever = vector_store.as_retriever(search_kwargs={"k": 3, "filter": metadata_filter} if metadata_filter else {"k": 3})
            llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
            qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever, return_source_documents=True)
            result = qa_chain({"query": question})

        st.subheader("💡 답변")
        st.write(result["result"])

        with st.expander("🔍 참조한 문서 내용 보기"):
            for i, doc in enumerate(result["source_documents"], 1):
                st.markdown(f"**참조 청크 {i} (출처: {doc.metadata.get('source')}, 청크 번호: {doc.metadata.get('chunk')}):**\n{doc.page_content}")
```


***

#### 주요 확장 사용법

- **PDF 폴더를 드래그\&드롭 or 다중 파일 업로드**
- 각 PDF는 내부적으로 여러 chunk로 분리되고, 각각에 원본 파일명/청크 번호 메타데이터가 추가됨
- Pinecone에는 벡터와 함께 메타데이터가 저장되어서,
입력란에서 `source:파일명.pdf` 등으로 **특정 파일(또는 특정 chunk)**에 한정하여 질의를 할 수 있음
- 메타데이터 필드를 여러 개 추가(예: 페이지 번호, 분류 등)하여 필터링 대상을 다양하게 확장할 수 있음[^4_1][^4_2][^4_3]

***

#### 참고/확장

- Google Drive 연동, 자동 폴더 모니터링, 대용량 데이터 파이프라인도 동일 구조로 확장 가능
- 메타데이터 필터는 Pinecone의 성능과 LangChain의 문서 API가 기본 지원(필터 구조는 Dict 타입으로 입력)[^4_4][^4_1]
- Word, 한글, txt 등 포맷 추가, 비동기 ingestion, chunk별 태깅 등도 유사하게 구현 가능

***

이 구조로 대규모 문서 RAG, 실무용 QA 서비스, 관리자용 검색 엔진 등 **범용적 확장이 가능합니다.**

[^4_2][^4_3][^4_1]
<span style="display:none">[^4_10][^4_5][^4_6][^4_7][^4_8][^4_9]</span>

<div align="center">⁂</div>

[^4_1]: https://docs.pinecone.io/integrations/langchain

[^4_2]: https://python.langchain.com/docs/integrations/document_loaders/unstructured_pdfloader/

[^4_3]: https://n8n.io/workflows/5085-convert-tour-pdfs-to-vector-database-using-google-drive-langchain-and-openai/

[^4_4]: https://docs.pinecone.io

[^4_5]: https://python.langchain.com/docs/integrations/vectorstores/pinecone/

[^4_6]: https://langchain-opentutorial.gitbook.io/langchain-opentutorial/09-vectorstore/04-pinecone

[^4_7]: https://stackoverflow.com/questions/76401057/why-does-pinecone-repeatedly-return-the-same-result-from-my-series-of-documents

[^4_8]: https://www.youtube.com/watch?v=erUfLIi9OFM

[^4_9]: https://python.langchain.com/docs/tutorials/rag/

[^4_10]: https://docs.llamaindex.ai/en/v0.10.33/examples/vector_stores/pinecone_metadata_filter/


---

# OPENAI\_API\_KEY, PINECONE\_API\_KEY, PINECONE\_ENVIRONMENT 발급방법을 알려주세요. 그리고 무료 LLM을 조사하고, API\_KEY를 발급 및 사용방법을 알려주세요.

아래에서 OpenAI, Pinecone API 키/환경 발급 방법과 무료 LLM 서비스, 각각의 API Key 발급 및 사용법을 체계적으로 안내합니다.

***

## 1. OPENAI_API_KEY 발급 방법

1. **OpenAI 계정 생성/로그인**
    - https://platform.openai.com/account/api-keys 접속
    - 회원 가입/로그인
2. **API Key 생성**
    - ‘Create new secret key’ 버튼 클릭
    - 원하는 Key 이름 입력 → 생성, 복사 (이후엔 키 전체를 다시 볼 수 없으니 꼭 안전 저장)
    - 해당 키는 OpenAI API를 사용하는 데 필요
3. **사용 예시 (Python)**

```python
import openai
openai.api_key = "발급받은_키"
# 또는 안전하게 환경변수로 관리
# os.environ.get('OPENAI_API_KEY')
```

    - 개발에선 환경변수(.env)에 저장해 사용하는 게 보안상 안전합니다.[^5_1][^5_2][^5_3][^5_4]

***

## 2. PINECONE_API_KEY \& PINECONE_ENVIRONMENT 발급 방법

1. **계정 생성/로그인**
    - https://app.pinecone.io/ 접속 후 회원 가입 및 로그인
2. **API Key 발급**
    - 대시보드 왼쪽 메뉴에서 Projects → 본인 프로젝트 선택
    - "API Keys" 항목으로 이동
    - 'Generate API Key' 클릭 → 이름 지정 후 생성 및 복사
    - 필요 시 권한 선택(읽기/쓰기 등)[^5_5][^5_6][^5_7]
3. **Environment(환경) 확인**
    - 같은 프로젝트 화면에서 Environment(예: us-west1-gcp-free, gcp-starter 등) 표기 확인
    - 각 인덱스/프로젝트별로 environment 값이 다를 수 있으니, 설정 탭에서 값 복사[^5_8][^5_9]

***

## 3. 무료 LLM API 및 API Key 발급/사용법

### 대표 무료·Freemium LLM API (2025년 기준)

| 서비스명 | 특이점/쿼터 | API Key 발급 및 사용법 |
| :-- | :-- | :-- |
| **OpenRouter** | 다양한 모델(무료/유료 혼합), 단일 키 | https://openrouter.ai/ 회원가입 → API Key 발급 → OpenAI 호환 API와 동일하게 사용[^5_10] |
| **Gemini Pro** | 구글, 최대 60QPM(쿼리/분) 무료 | Google Cloud 계정 생성 → Cloud Console에서 "Gemini" API Key 발급[^5_11] |
| **Together AI** | 25달러 크레딧/무료 쿼터, Llama2 지원 | https://www.together.ai/ 가입 → 대시보드에서 API Key 발급[^5_11][^5_12][^5_13] |
| **Shale Protocol** | Llama2 무료 사용 | https://shaleprotocol.com 회원가입 → Key 발급[^5_11] |
| **ArliAI** | 제한 없는 무료 사용 | https://arliAI.com → 계정 생성 후 Key 복사[^5_11] |
| **Mistral AI (mistral.ai)** | 무료 패키지 있음 | https://platform.mistral.ai/ 회원가입 후 Key 발급[^5_13] |

> 더 많은 무료 LLM 제공 업체들이 있으니, 아래 리스트/깃허브 참고.[^5_14][^5_12][^5_13]

### 일반적인 API Key 사용 예시 (OpenRouter/ArliAI 등)

```python
import openai

openai.api_key = "본인_API_KEY"
openai.api_base = "https://openrouter.ai/api/v1"  # 서비스별 엔드포인트 확인
```

- Service별로 OpenAI 호환 API 구조(openai.ChatCompletion 등)로 거의 동일하게 사용 가능
- 각 서비스별 문서의 예시 curl, Python 샘플 코드 참고

***

## 참고

- OpenAI: 평판이 높으나 무료 크레딧은 제공하지 않음. 기본이 유료
- Pinecone: 무료 플랜(Starter/Trial) 존재, 사용량 제한 있음
- 무료 LLM 대부분 쿼터/속도, 일일 제한 등이 있으니 문서 및 FAQ 확인 권장
- API Key는 코드에 하드코딩하지 말고 환경변수/Secret Manager 등 안전하게 보관하세요

***

**궁금한 점이나 특정 서비스의 샘플 코드 등 추가 안내 필요하면 요청해 주세요!**

[^5_2][^5_11][^5_10][^5_6][^5_3][^5_12][^5_4][^5_9][^5_13][^5_7][^5_1][^5_8][^5_5][^5_14]
<span style="display:none">[^5_15][^5_16][^5_17][^5_18][^5_19][^5_20]</span>

<div align="center">⁂</div>

[^5_1]: https://help.openai.com/en/articles/4936850-where-do-i-find-my-openai-api-key

[^5_2]: https://wikidocs.net/196075

[^5_3]: https://platform.openai.com/docs/quickstart/create-and-export-an-api-key

[^5_4]: https://addepto.com/blog/what-is-an-openai-api-and-how-to-use-it/

[^5_5]: https://docs.pinecone.io/guides/projects/manage-api-keys

[^5_6]: https://www.gitguardian.com/remediation/pinecone-api-key-and-environment

[^5_7]: https://docs.pinecone.io/reference/api/authentication

[^5_8]: https://docs.gitguardian.com/secrets-detection/secrets-detection-engine/detectors/specifics/pinecone_api_keys

[^5_9]: https://community.pinecone.io/t/changing-the-environment-the-the-api-key/1020

[^5_10]: https://cylab.be/blog/432/using-openrouter-for-single-api-key-access-to-all-your-llm-models

[^5_11]: https://www.reddit.com/r/MachineLearning/comments/1au64x1/d_are_there_any_free_llms_for_developers_with_api/

[^5_12]: https://github.com/cheahjs/free-llm-api-resources

[^5_13]: https://coaxsoft.com/blog/llm-api-comparison

[^5_14]: https://apidog.com/blog/free-open-source-llm-apis/

[^5_15]: https://platform.openai.com/api-keys

[^5_16]: https://platform.openai.com/docs/quickstart

[^5_17]: https://www.youtube.com/watch?v=dJ5aIRUyhNA

[^5_18]: https://community.openai.com/t/how-do-i-get-my-api-key/29343

[^5_19]: https://www.youtube.com/watch?v=SzPE_AE0eEo

[^5_20]: https://docs.pinecone.io/guides/get-started/quickstart

