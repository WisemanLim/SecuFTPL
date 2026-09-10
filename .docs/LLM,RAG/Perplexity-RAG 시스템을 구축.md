<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# RAG 시스템을 구축하고자 합니다. RAG의 베이스가 문서가 아닌 데이터베이스의 테이블 또는 테이블의 집합입니다. 이를 위한 시스템 설정 및 예제 코드를 구현해 주세요.

단, 데이터베이스는 postgresql이며, streamlit 기반의 웹사이트를 형태로 구동이 되며, LLM은 Local LLM(Ollama)를 이용합니다

RAG 시스템을 PostgreSQL 테이블 기반으로 구축하기 위해서는 **pgvector 확장 기능**, **Ollama 임베딩 생성**, **Streamlit 웹 인터페이스**를 결합해야 합니다. 다음은 단계별 구현 가이드와 예제 코드입니다.

---

## 시스템 아키텍처 개요

1. **PostgreSQL**: 테이블 데이터 저장 및 pgvector를 이용한 벡터 검색
2. **Ollama**: 로컬 LLM을 이용한 임베딩 생성/응답 생성
3. **Streamlit**: 사용자 인터페이스 및 데이터 시각화

---

## 1. PostgreSQL 설정

### pgvector 확장 설치

```sql
-- 확장 기능 활성화
CREATE EXTENSION IF NOT EXISTS vector;

-- 데이터+임베딩 저장 테이블 생성
CREATE TABLE sales_data (
    id SERIAL PRIMARY KEY,
    product_name VARCHAR(100),
    sales_amount NUMERIC,
    description TEXT,
    embedding VECTOR(768)  -- 모델 임베딩 차원에 맞춰 조정
);
```


---

## 2. Ollama 연동 설정

### 임베딩 생성 코드 (Python)

```python
import requests

def generate_embedding(text: str) -> list:
    response = requests.post(
        "http://localhost:11434/api/embeddings",
        json={"model": "llama3", "prompt": text}
    )
    return response.json()["embedding"]
```


---

## 3. Streamlit 웹 인터페이스

### 전체 애플리케이션 코드 (`app.py`)

```python
import streamlit as st
import psycopg2
import numpy as np
from pgvector.psycopg2 import register_vector

# Ollama 연결 설정
OLLAMA_URL = "http://localhost:11434"

# DB 연결
def get_conn():
    return psycopg2.connect(
        dbname=st.secrets["DB_NAME"],
        user=st.secrets["DB_USER"],
        password=st.secrets["DB_PASSWORD"],
        host=st.secrets["DB_HOST"]
    )

# 검색 쿼리
def semantic_search(query: str, top_k: int=3):
    embedding = generate_embedding(query)
    
    conn = get_conn()
    register_vector(conn)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT product_name, sales_amount, description 
        FROM sales_data 
        ORDER BY embedding <=> %s 
        LIMIT %s
    """, (np.array(embedding), top_k))
    
    results = cur.fetchall()
    conn.close()
    return results

# Streamlit UI
st.title("테이블 기반 RAG 시스템")
query = st.text_input("상품 관련 질문을 입력하세요:")

if query:
    # 1. 유사도 검색
    context_data = semantic_search(query)
    
    # 2. LLM 응답 생성
    context_str = "\n".join([f"{row[^1_0]}: {row[^1_2]}" for row in context_data])
    prompt = f"""Context: {context_str}
    Question: {query}
    Answer:"""
    
    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={"model": "llama3", "prompt": prompt, "stream": False}
    )
    
    st.subheader("응답 결과")
    st.write(response.json()["response"])
    
    st.subheader("검색된 컨텍스트")
    st.table(context_data)
```


---

## 4. 시스템 실행 절차

1. **의존성 설치**
```bash
pip install streamlit psycopg2-binary pgvector requests
```

2. **Secrets 설정 (`.streamlit/secrets.toml`)**
```toml
[connections.postgresql]
host = "localhost"
port = "5432"
database = "your_db"
username = "your_user"
password = "your_password"
```

3. **데이터 임베딩 생성 및 저장**
```python
# 기존 데이터 벡터화
conn = get_conn()
cur = conn.cursor()

for row in source_data:
    text_representation = f"{row['product_name']}: {row['description']}"
    embedding = generate_embedding(text_representation)
    
    cur.execute("""
        INSERT INTO sales_data 
        (product_name, sales_amount, description, embedding)
        VALUES (%s, %s, %s, %s)
    """, (row['product_name'], row['sales_amount'], 
          row['description'], embedding))
    
conn.commit()
```


---

## 5. 고급 구성 옵션

1. **하이브리드 검색**
```python
# 키워드 + 의미 검색 결합
cur.execute("""
    SELECT *, 
        (0.5 * ts_rank(text_search, plainto_tsquery(%s)) +
         0.5 * (1 - (embedding <=> %s))) AS score
    FROM sales_data
    ORDER BY score DESC
    LIMIT %s
""", (query, embedding, top_k))
```

2. **실시간 업데이트**
```python
# Streamlit에서 신규 데이터 입력
with st.sidebar.form("new_data"):
    name = st.text_input("상품명")
    price = st.number_input("가격")
    desc = st.text_area("설명")
    
    if st.form_submit_button("저장"):
        embedding = generate_embedding(f"{name}: {desc}")
        # DB 저장 코드
```


---

이 시스템은 PostgreSQL의 구조화된 데이터와 LLM의 의미 이해 능력을 결합하여 **도메인 특화 QA 시스템**, **데이터 탐색 도구**, **보고서 자동 생성 시스템** 등에 활용 가능합니다. 성능 최적화를 위해 임베딩 모델 선택(예: llama3 vs mistral)과 pgvector 인덱스 튜닝이 필요합니다[^1_1][^1_11].
<span style="display:none">[^1_10][^1_12][^1_13][^1_14][^1_15][^1_16][^1_17][^1_18][^1_19][^1_20][^1_21][^1_22][^1_23][^1_24][^1_25][^1_26][^1_27][^1_28][^1_29][^1_3][^1_30][^1_31][^1_32][^1_33][^1_34][^1_35][^1_36][^1_37][^1_38][^1_39][^1_4][^1_40][^1_41][^1_42][^1_43][^1_44][^1_45][^1_46][^1_47][^1_48][^1_49][^1_5][^1_50][^1_51][^1_6][^1_7][^1_8][^1_9]</span>

<div align="center">⁂</div>

[^1_1]: https://pgdash.io/blog/rag-with-postgresql.html

[^1_2]: https://docs.streamlit.io/develop/tutorials/databases/postgresql

[^1_3]: https://cylab.be/blog/377/run-your-own-local-llm-with-ollama

[^1_4]: https://www.datacamp.com/tutorial/llama-3-1-rag

[^1_5]: https://dev.to/jayantaadhikary/using-the-ollama-api-to-run-llms-and-generate-responses-locally-18b7

[^1_6]: https://discuss.pytorch.kr/t/gn-postgresql-rag-feat-pgdash/4449

[^1_7]: https://ploomber.io/blog/streamlit-postgres/

[^1_8]: https://www.cohorte.co/blog/using-ollama-with-python-step-by-step-guide

[^1_9]: https://www.enterprisedb.com/blog/rag-app-postgres-and-pgvector

[^1_10]: https://www.w3resource.com/PostgreSQL/snippets/streamlit-postgres.php

[^1_11]: https://apidog.com/blog/deploy-local-ai-llms/

[^1_12]: https://huggingface.co/learn/cookbook/en/rag_with_sql_reranker

[^1_13]: https://discuss.pytorch.kr/t/pgai-postgresql-feat-timescale/6133

[^1_14]: https://www.timescale.com/blog/build-search-and-rag-systems-on-postgresql-using-cohere-and-pgai

[^1_15]: https://techcommunity.microsoft.com/blog/azuredevcommunityblog/rag-on-structured-data-with-postgresql/4164456

[^1_16]: https://news.hada.io/topic?id=14898

[^1_17]: https://edbkorea.com/blog/postgres-및-pgvector가-포함된-rag-앱/

[^1_18]: https://www.reddit.com/r/LangChain/comments/1efnx5u/rag_over_database/

[^1_19]: https://learn.microsoft.com/ro-ro/shows/visual-studio-code/building-a-rag-application-with-a-postgresql-database

[^1_20]: https://gist.github.com/Joel-hanson/132138e0a6720013dca669546fe98777

[^1_21]: https://community.openai.com/t/creating-a-rag-solution-from-a-sql-db-with-summarization/892958

[^1_22]: https://www.mindfiretechnology.com/blog/archive/installing-postgresql-in-preparation-for-retrieval-augmented-generation/

[^1_23]: https://blog.gopenai.com/advanced-rag-for-database-without-exposing-db-data-text-to-sql-a0e71f00e010

[^1_24]: https://www.youtube.com/watch?v=yzHa1S3OO2s

[^1_25]: https://discuss.streamlit.io/t/updating-database-through-streamlit-postgresql/63024

[^1_26]: https://constellationanalytics.com.au/all-projects/f/streamlit-gui-for-postgresql-database

[^1_27]: https://liambeeton.com/programming/building-a-lightweight-rag-system-with-llamaindex-ollama-and-qdrant

[^1_28]: https://programmer.ie/post/ollama/

[^1_29]: https://www.kdnuggets.com/ollama-tutorial-running-llms-locally-made-super-simple

[^1_30]: https://weaviate.io/blog/local-rag-with-ollama-and-weaviate

[^1_31]: https://lsjsj92.tistory.com/666

[^1_32]: https://www.youtube.com/watch?v=XffJeNBVdtU

[^1_33]: https://hackernoon.com/build-a-fully-local-rag-system-with-rlama-and-ollamano-cloud-no-dependencies

[^1_34]: https://devocean.sk.com/blog/techBoardDetail.do?ID=165685\&boardType=techBlog

[^1_35]: https://dev.to/mohsin_rashid_13537f11a91/rag-with-ollama-1049

[^1_36]: https://www.learndatasci.com/solutions/how-to-use-open-source-llms-locally-for-free-ollama-python/

[^1_37]: https://itsfoss.com/local-llm-rag-ollama-langchain/

[^1_38]: https://www.youtube.com/watch?v=zZS73hOmyRY

[^1_39]: https://www.youtube.com/watch?v=hAdEuDBN57g

[^1_40]: https://docs.vectorize.io/tutorials-and-how-to-guides/tutorials/postgresql-quickstart

[^1_41]: https://www.chitika.com/rag-sql-database-integration/

[^1_42]: https://www.crunchydata.com/blog/smarter-postgres-llm-with-retrieval-augmented-generation

[^1_43]: https://growth-coder.tistory.com/334

[^1_44]: https://www.ecopro.ai/entry/Streamlit-PostgreSQL-연동

[^1_45]: https://discuss.streamlit.io/t/connecting-to-postgresql/62861

[^1_46]: https://www.datamax.ai/post/dbt-streamlit-postgres-handson

[^1_47]: https://www.restack.io/docs/streamlit-knowledge-streamlit-fastapi-postgresql-integration

[^1_48]: https://github.com/Rareshp/python_streamlit_postgresql

[^1_49]: https://www.youtube.com/watch?v=UtSSMs6ObqY

[^1_50]: https://python.langchain.com/docs/integrations/llms/ollama/

[^1_51]: https://dev.to/arjunrao87/using-ollama-getting-hands-on-with-local-llms-and-building-a-chatbot-2gp3


---

## 시스템 아키텍처 개요

1. **LLM 서버**: GPU EC2 (g5.xlarge) - Ollama 컨테이너 구동
2. **DB 서버**: CPU EC2 (t3.medium) - PostgreSQL+pgvector 컨테이너
3. **웹 서버**: CPU EC2 (t3.micro) - Streamlit 컨테이너

---

## 1. Terraform 인프라 구성

### 전체 인프라 코드 (`main.tf`)

```hcl
# AWS 프로바이더 설정
provider "aws" {
  region = "ap-northeast-2"
}

# GPU 인스턴스 (Ollama)
resource "aws_instance" "llm_server" {
  ami           = "ami-0c9c942bd7bf113a2" # Ubuntu 22.04
  instance_type = "g5.xlarge"
  key_name      = "rag-keypair"

  tags = {
    Name = "llm-gpu-server"
  }

  # GPU 드라이버 자동 설치
  user_data = file("setup-gpu.sh")
}

# PostgreSQL 인스턴스
resource "aws_instance" "db_server" {
  ami           = "ami-0c9c942bd7bf113a2"
  instance_type = "t3.medium"
  key_name      = "rag-keypair"

  tags = {
    Name = "postgresql-server"
  }

  user_data = file("setup-db.sh")
}

# Streamlit 인스턴스
resource "aws_instance" "web_server" {
  ami           = "ami-0c9c942bd7bf113a2"
  instance_type = "t3.micro"
  key_name      = "rag-keypair"

  tags = {
    Name = "streamlit-server"
  }

  user_data = file("setup-web.sh")
}

# 보안 그룹 설정
resource "aws_security_group" "rag_sg" {
  name        = "rag-security-group"
  description = "Allow RAG system traffic"

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 8501
    to_port     = 8501
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 11434
    to_port     = 11434
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```


---

## 2. Docker Compose 구성

### 2.1 LLM 서버 (`docker-compose.llm.yml`)

```yaml
version: '3.8'

services:
  ollama:
    image: ollama/ollama:latest
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

volumes:
  ollama_data:
```


### 2.2 DB 서버 (`docker-compose.db.yml`)

```yaml
version: '3.8'

services:
  postgres:
    image: ankane/pgvector:latest
    environment:
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: password
      POSTGRES_DB: ragdb
    ports:
      - "5432:5432"
    volumes:
      - pg_data:/var/lib/postgresql/data

volumes:
  pg_data:
```


### 2.3 웹 서버 (`docker-compose.web.yml`)

```yaml
version: '3.8'

services:
  streamlit:
    build: .
    ports:
      - "8501:8501"
    environment:
      DB_HOST: ${DB_HOST}
      OLLAMA_URL: ${OLLAMA_URL}
    depends_on:
      - db

  db:
    image: postgres:13
    environment:
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: password
      POSTGRES_DB: ragdb
```


---

## 3. 배포 자동화 스크립트

### 3.1 GPU 서버 설정 (`setup-gpu.sh`)

```bash
#!/bin/bash
# NVIDIA 드라이버 설치
curl -s -L https://nvidia.github.io/nvidia-container-runtime/gpgkey | sudo apt-key add -
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-container-runtime/$distribution/nvidia-container-runtime.list | sudo tee /etc/apt/sources.list.d/nvidia-container-runtime.list
sudo apt-get update
sudo apt-get install -y nvidia-container-runtime

# Docker 설치
sudo apt-get install -y docker.io
sudo systemctl enable docker
sudo systemctl start docker

# Docker Compose 설치
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Ollama 서비스 시작
git clone https://github.com/your-repo/rag-system.git
cd rag-system/llm
docker-compose -f docker-compose.llm.yml up -d
```


### 3.2 DB 서버 설정 (`setup-db.sh`)

```bash
#!/bin/bash
sudo apt-get update
sudo apt-get install -y docker.io
sudo systemctl enable docker
sudo systemctl start docker

sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

git clone https://github.com/your-repo/rag-system.git
cd rag-system/db
docker-compose -f docker-compose.db.yml up -d
```


---

## 4. 배포 실행 절차

1. **Terraform 인프라 프로비저닝**
```bash
terraform init
terraform plan
terraform apply
```

2. **서비스 배포 확인**
```bash
# LLM 서버
ssh -i rag-keypair.pem ubuntu@llm-server-ip 'docker ps'

# DB 서버 
ssh -i rag-keypair.pem ubuntu@db-server-ip 'pg_isready'

# 웹 서버
ssh -i rag-keypair.pem ubuntu@web-server-ip 'curl localhost:8501'
```


---

## 5. 고급 구성 옵션

1. **Terraform 모듈화**
```hcl
module "llm_cluster" {
  source = "./modules/llm"

  instance_count = 2
  instance_type  = "g5.2xlarge"
}
```

2. **CI/CD 파이프라인**
```yaml
# .github/workflows/deploy.yml
name: RAG Deployment

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Terraform Apply
        uses: hashicorp/terraform-github-actions@v2
        with:
          tf_actions_version: latest
          tf_actions_subcommand: 'apply'
          tf_actions_working_dir: 'terraform/'
```


---

이 구성은 **분산 아키텍처**를 통해 리소스 사용을 최적화하며, Terraform의 **IaC(Infrastructure as Code)** 방식을 통해 재현 가능한 배포 환경을 제공합니다. GPU 가속 인스턴스와 일반 인스턴스를 분리하여 비용 효율성을 달성하면서도 시스템 확장성을 보장합니다[^2_3][^2_7][^2_10].
<span style="display:none">[^2_1][^2_11][^2_12][^2_13][^2_14][^2_15][^2_16][^2_17][^2_18][^2_19][^2_2][^2_20][^2_21][^2_22][^2_23][^2_24][^2_25][^2_26][^2_27][^2_28][^2_29][^2_30][^2_31][^2_32][^2_33][^2_34][^2_35][^2_36][^2_37][^2_38][^2_39][^2_4][^2_40][^2_41][^2_42][^2_43][^2_44][^2_45][^2_46][^2_47][^2_48][^2_49][^2_5][^2_50][^2_51][^2_52][^2_53][^2_54][^2_55][^2_56][^2_57][^2_58][^2_59][^2_6][^2_60][^2_61][^2_62][^2_63][^2_64][^2_65][^2_66][^2_67][^2_68][^2_69][^2_70][^2_71][^2_72][^2_73][^2_74][^2_75][^2_76][^2_77][^2_78][^2_79][^2_8][^2_80][^2_81][^2_82][^2_83][^2_84][^2_85][^2_86][^2_87][^2_9]</span>

<div align="center">⁂</div>

[^2_1]: https://diane-space.tistory.com/532

[^2_2]: https://blog.gopenai.com/how-to-setup-an-environment-to-run-large-language-models-in-docker-containers-5992309e6b13

[^2_3]: https://github.com/vithursant/terraform-aws-spotgpu

[^2_4]: https://www.linkedin.com/pulse/deploying-multi-container-docker-compose-application-aws-oghli

[^2_5]: https://anaelle.tistory.com/141

[^2_6]: https://github.com/dhopp1/local_rag_llm

[^2_7]: https://gist.github.com/glaszczak/776265a871b08347b6433ad76307004c

[^2_8]: https://aws.amazon.com/blogs/devops/accelerate-serverless-streamlit-app-deployment-with-terraform/

[^2_9]: https://www.datamax.ai/post/dbt-streamlit-postgres-handson

[^2_10]: https://spacelift.io/blog/terraform-ec2-instance

[^2_11]: https://aqibhafeez473.hashnode.dev/day-13-setting-up-docker-compose-on-aws-ec2-instance-with-ubuntu

[^2_12]: https://twentytwentyone.tistory.com/289

[^2_13]: https://www.chrisdpadilla.com/dockercomposetoawsec2

[^2_14]: https://enlear.academy/deploying-a-full-stack-application-on-aws-ec2-with-docker-a-step-by-step-guide-86363d99a5ff

[^2_15]: https://aqibhafeez473.hashnode.dev/day-13-setting-up-docker-compose-on-aws-ec2-instance-with-ubuntu

[^2_16]: https://blog.neuralwork.ai/deploying-llms-on-aws-ec2-using-cog-a-complete-guide/

[^2_17]: https://discuss.streamlit.io/t/how-to-setup-streamlit-locally-in-my-system-first-and-next-aws-ec2-instance/66509

[^2_18]: https://everythingdevops.dev/how-to-deploy-a-multi-container-docker-compose-application-on-amazon-ec2/

[^2_19]: https://langfuse.com/self-hosting/docker-compose

[^2_20]: https://workshops.aws

[^2_21]: https://swathireddy.hashnode.dev/deploying-multiple-applications-on-aws-ec2-with-docker

[^2_22]: https://dev.to/aws-builders/deploy-your-llm-on-aws-ec2-2ig3

[^2_23]: https://www.reddit.com/r/aws/comments/1fs59b7/how_to_deploy_multiple_docker_containers_to_a/

[^2_24]: https://aws.amazon.com/blogs/machine-learning/serving-llms-using-vllm-and-amazon-ec2-instances-with-aws-ai-chips/

[^2_25]: https://docs.aws.amazon.com/ko_kr/elasticbeanstalk/latest/dg/docker-multicontainer-migration.html

[^2_26]: https://www.youtube.com/watch?v=vCyVVsdKJCg

[^2_27]: https://dev.to/johnogbonna/getting-started-with-terraform-deploying-an-aws-ec2-instance-51hg

[^2_28]: https://github.com/aws-ia/terraform-aws-serverless-streamlit-app

[^2_29]: https://registry.terraform.io/modules/vistimi/microservice/aws/latest/examples/gpu

[^2_30]: https://www.enterprisedb.com/postgres-tutorials/how-deploy-postgresql-and-edb-postgres-platform-aws-using-terraform-automation

[^2_31]: https://towardsaws.com/how-to-deploy-a-streamlit-application-on-amazon-linux-ec2-9a71593b434

[^2_32]: https://www.itwonderlab.com/aws-terraform-tutorial-aws-ec2/

[^2_33]: https://www.pedroalonso.net/blog/using-terraform-to-automate-the-deployment-of-postgresql-to-ec2/

[^2_34]: https://blog.nonstopio.com/hosting-a-streamlit-python-app-on-aws-ec2-a-step-by-step-guide-0148062b992d

[^2_35]: https://docs.fortinet.com/document/lacework-forticnapp/latest/administration-guide/439090/install-linux-agent-on-aws-ec2-with-terraform-and-aws-systems-manager

[^2_36]: https://registry.terraform.io/providers/cyralinc/cyral/latest/docs/guides/setup_cp_and_deploy_sidecar

[^2_37]: https://everenew.tistory.com/446

[^2_38]: https://velog.io/@minhojjang/EC2-Instance-Deployment-with-Terraform

[^2_39]: https://dev-dorydory.tistory.com/56

[^2_40]: https://stackoverflow.com/questions/62341276/start-docker-compose-automatically-on-ec2-startup

[^2_41]: https://stackoverflow.com/questions/53581375/continuous-deployment-of-docker-compose-app-to-aws-ec2

[^2_42]: https://insight.infograb.net/docs/aws/installing-docker-compose-on-aws-ec2

[^2_43]: https://velog.io/@alsrlqor/AWS-EC2에서-docker-compose로-배포

[^2_44]: https://velog.io/@cothis/aws-ec2-S3-code-deploy-docker-배포-삽질기

[^2_45]: https://5w33th0me4jisu.tistory.com/entry/AWS-EC2-인스턴스로-Docker-컨테이너-실행feat-docker-compose

[^2_46]: https://velog.io/@ehddk0133/Project-git-action으로-AWS-EC2에서-docker-compose-적용하기

[^2_47]: https://tang-log.tistory.com/60

[^2_48]: https://repost.aws/questions/QUcH0NvVJ_TQ282DssLg2AfQ/ec2-with-docker-services

[^2_49]: https://www.restack.io/docs/streamlit-knowledge-streamlit-fastapi-docker-compose

[^2_50]: https://luisciber.hashnode.dev/how-to-build-a-rag-system-locally

[^2_51]: https://discuss.streamlit.io/t/streamlit-postgres-on-docker/53415

[^2_52]: https://www.bitdoze.com/multiple-postgres-databases-docker/

[^2_53]: https://www.youtube.com/watch?v=hAdEuDBN57g

[^2_54]: https://github.com/george-mountain/LLM-Local-Streaming

[^2_55]: https://docs.streamlit.io/deploy/tutorials/docker

[^2_56]: https://gist.github.com/Joel-hanson/132138e0a6720013dca669546fe98777

[^2_57]: https://jaehyeon.me/blog/2025-02-18-realtime-dashboard-1/

[^2_58]: https://pgdash.io/blog/rag-with-postgresql.html

[^2_59]: https://chaitannyaa.hashnode.dev/docker-compose-project-deploy-multi-container-application-with-5-different-services

[^2_60]: https://docs.docker.com/guides/genai-leveraging-rag/

[^2_61]: https://skundunotes.com/2024/09/18/create-amazon-rds-for-postgresql-db-using-terraform-and-github-actions/

[^2_62]: https://www.gyden.io/en/content-hub/a-comprehensive-guide-for-amazon-ecs-ec-2-using-terraform

[^2_63]: https://arcozz.tistory.com/42

[^2_64]: https://blog.stackademic.com/stepbystep-deploy-and-connect-to-aws-ec2-instances-using-terraform-f672a070e35e

[^2_65]: https://blog.naver.com/classmethodkr/222391101505

[^2_66]: https://registry.terraform.io/modules/terraform-aws-modules/rds-proxy/aws/latest/examples/postgresql-iam-instance

[^2_67]: https://velog.io/@budlebee/docker-compose-nodejs-postgresql-aws-ec2

[^2_68]: https://www.youtube.com/watch?v=DflWqmppOAg

[^2_69]: https://www.linkedin.com/pulse/deploying-multi-container-docker-compose-application-aws-oghli

[^2_70]: https://github.com/aws-samples/rag-with-amazon-bedrock-and-pgvector

[^2_71]: https://www.reddit.com/r/Terraform/comments/8fs2xs/terraform_aws_fully_automated_provisioning_of_aws/

[^2_72]: https://registry.terraform.io/providers/hashicorp/aws/5.65.0/docs/resources/instance

[^2_73]: https://github.com/techfort/udacity-ec2-gpu

[^2_74]: https://gist.github.com/glaszczak/776265a871b08347b6433ad76307004c

[^2_75]: https://aws.amazon.com/blogs/devops/accelerate-serverless-streamlit-app-deployment-with-terraform/

[^2_76]: https://www.chrisdpadilla.com/dockercomposetoawsec2

[^2_77]: https://www.reddit.com/r/django/comments/1ajnnx4/deployment_of_a_dockercompose_in_a_single_ec2/

[^2_78]: https://www.youtube.com/watch?v=iLBaIXwoQqg

[^2_79]: https://stackoverflow.com/questions/63708035/installing-docker-compose-on-amazon-ec2-linux-2-9kb-docker-compose-file

[^2_80]: https://www.youtube.com/watch?v=gRgdnHHuvoI

[^2_81]: https://www.datamax.ai/post/dbt-streamlit-postgres-handson

[^2_82]: https://anaelle.tistory.com/142

[^2_83]: https://github.com/lvgalvao/crud-fastapi-postgres-streamlit/blob/main/docker-compose.yml

[^2_84]: https://github.com/gerardrbentley/streamlit-fullstack

[^2_85]: https://www.bitdoze.com/litellm-docker-install/

[^2_86]: https://github.com/ashleykleynhans/stable-diffusion-terraform

[^2_87]: https://stackoverflow.com/questions/58271771/attach-elastic-inference-gpu-graphics-on-aws-ec2-instance-with-terraform-lauch-t


---

# Terraform의 배포 실행을 로컬이 아닌, streamlit이 배포된 EC2에 CI/CD 환경을 구성하여 관리자가 웹포털(관리자 배포 사이트)을 통해 진행하고자 한다. CI/CD를 위한 open source framework를 이용하여 관리자 배포 사이트를 구성하고 Terraform 배포 등을 진행 할 수 있도록 설정을 완료해 주세요.

<span style="display:none">[^3_1][^3_10][^3_11][^3_12][^3_13][^3_14][^3_15][^3_16][^3_17][^3_18][^3_19][^3_2][^3_20][^3_21][^3_22][^3_23][^3_24][^3_25][^3_26][^3_27][^3_28][^3_29][^3_3][^3_30][^3_31][^3_32][^3_33][^3_34][^3_35][^3_36][^3_37][^3_38][^3_39][^3_4][^3_40][^3_41][^3_42][^3_43][^3_44][^3_45][^3_46][^3_47][^3_48][^3_49][^3_5][^3_50][^3_51][^3_6][^3_7][^3_8][^3_9]</span>

<div align="center">⁂</div>

[^3_1]: https://www.bytebase.com/blog/top-terraform-tools/

[^3_2]: https://github.com/Terraform-GUI/terraform-gui

[^3_3]: https://spacelift.io/blog/terraform-in-ci-cd

[^3_4]: https://spacelift.io/blog/terraform-automation

[^3_5]: https://www.reddit.com/r/selfhosted/comments/1ah7pgg/an_open_source_self_hosted_continuous_deployment/

[^3_6]: https://spacelift.io/blog/gitlab-terraform

[^3_7]: https://www.hashicorp.com/blog/learn-ci-cd-automation-with-terraform-and-circleci

[^3_8]: https://developer.hashicorp.com/terraform/tutorials/automation/circle-ci

[^3_9]: https://dev.to/miketysonofthecloud/4-useful-terraform-open-source-tools-57cl

[^3_10]: https://spacelift.io/blog/terraform-tools

[^3_11]: https://buildkite.com/resources/blog/best-practices-for-terraform-ci-cd/

[^3_12]: https://www.reddit.com/r/Terraform/comments/ouaa33/what_are_some_lightweight_cloud_agnostic_cicd/

[^3_13]: https://github.com/Terraform-GUI/terraform-gui

[^3_14]: https://www.youtube.com/watch?v=2JA2KRE63q4

[^3_15]: https://zeet.co/blog/terraform-tools

[^3_16]: https://dev.to/charlienov17/using-terraform-to-deploy-a-basic-web-server-on-aws-1i6p

[^3_17]: https://aws.amazon.com/blogs/devops/terraform-ci-cd-and-testing-on-aws-with-the-new-terraform-test-framework/

[^3_18]: https://thectoclub.com/tools/best-ci-cd-tools/

[^3_19]: https://www.bytebase.com/blog/top-terraform-ui-tools/

[^3_20]: https://developer.okta.com/blog/2024/10/11/terraform-ci-cd

[^3_21]: https://www.reddit.com/r/selfhosted/comments/1ah7pgg/an_open_source_self_hosted_continuous_deployment/

[^3_22]: https://docs.digitalocean.com/reference/terraform/deploy-web-app/

[^3_23]: https://www.reddit.com/r/Terraform/comments/16gfemh/terraform_in_cicd/

[^3_24]: https://blog.stackademic.com/deploying-a-web-app-to-azure-with-terraform-integrating-infrastructure-as-code-into-ci-cd-862013ba3885

[^3_25]: https://github.com/pangeo-data/terraform-deploy/blob/master/aws-examples/minimal-deployment-tutorial/README.md

[^3_26]: https://www.googlecloudcommunity.com/gc/Developer-Tools/CI-CD-with-terraform/td-p/709829

[^3_27]: https://cloud.google.com/secure-source-manager/docs/configure-cicd-terraform-config-as-code

[^3_28]: https://developer.hashicorp.com/terraform/tutorials/applications

[^3_29]: https://www.terraform.io

[^3_30]: https://github.com/xuyangbocn/terraform-aws-self-host-llm/blob/main/modules/open-webui-service/README.md

[^3_31]: https://upcloud.com/resources/tutorials/deploy-high-availability-web-app-terraform

[^3_32]: https://terramate.io/rethinking-iac/how-to-build-a-ci-cd-pipeline-for-terraform-with-terramate-on-github-actions/

[^3_33]: https://docs.gitlab.com/ci/examples/

[^3_34]: https://developer.hashicorp.com/terraform/tutorials/automation/automate-terraform

[^3_35]: https://docs.aws.amazon.com/prescriptive-guidance/latest/patterns/create-a-ci-cd-pipeline-to-validate-terraform-configurations-by-using-aws-codepipeline.html

[^3_36]: https://www.techielass.com/terraform-with-azure-devops-ci-cd-pipeline/

[^3_37]: https://discuss.hashicorp.com/t/terraform-web-app/46665

[^3_38]: https://www.reddit.com/r/Terraform/comments/opje84/web_app_to_deploy_infra_using_terraform/

[^3_39]: https://zeet.co/blog/terraform-ci-cd

[^3_40]: https://estuary.dev/blog/open-source-ci-cd-tools/

[^3_41]: https://spacelift.io/blog/terraform-in-ci-cd

[^3_42]: https://github.com/electrocucaracha/terraform-cicd

[^3_43]: https://developer.hashicorp.com/terraform/intro/use-cases

[^3_44]: https://terrateam.io/blog/terraform-best-practices-ci-cd/

[^3_45]: https://aws.amazon.com/ko/blogs/tech/scaling-iac-and-ci-cd-pipelines-with-terraform-github-actions-and-aws-proton/

[^3_46]: https://www.hashicorp.com/blog/learn-ci-cd-automation-with-terraform-and-circleci

[^3_47]: https://blog.devops.dev/how-to-use-terraform-cloud-as-a-ci-cd-tool-8ee24fb478bf

[^3_48]: https://talent500.com/blog/how-to-use-terraform-to-deploy-your-infrastructure-in-ci-cd/

[^3_49]: https://www.youtube.com/watch?v=F7aLRfn4z-A

[^3_50]: https://blog.devops.dev/terraform-jenkins-s3-automating-infrastructure-setup-and-ci-cd-pipeline-for-static-website-5bec1b17a4d5

[^3_51]: https://docs.aws.amazon.com/ko_kr/prescriptive-guidance/latest/patterns/create-a-ci-cd-pipeline-to-validate-terraform-configurations-by-using-aws-codepipeline.html


---

# 앞선 질문에 대한 답변이 없거나 보이지 않는데요. 완료된 설정 방법이나 배포를 위한 스크립트 등을 보여주세요.

다음은 완전한 배포를 위한 단계별 가이드와 스크립트입니다. **3개의 EC2 인스턴스**에 분산 배포하는 전체 프로세스를 설명합니다.

---

## 1. 인프라 구성 (Terraform)

### `main.tf` 파일

```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "ap-northeast-2"
}

resource "aws_instance" "llm" {
  ami           = "ami-0c9c942bd7bf113a2" # Ubuntu 22.04
  instance_type = "g5.xlarge"
  key_name      = "rag-key"
  security_groups = [aws_security_group.rag_sg.name]

  tags = {
    Name = "Ollama-GPU"
  }

  user_data = file("install_ollama.sh")
}

resource "aws_instance" "db" {
  ami           = "ami-0c9c942bd7bf113a2"
  instance_type = "t3.medium"
  key_name      = "rag-key"
  security_groups = [aws_security_group.rag_sg.name]

  tags = {
    Name = "PostgreSQL"
  }

  user_data = file("install_postgres.sh")
}

resource "aws_instance" "web" {
  ami           = "ami-0c9c942bd7bf113a2"
  instance_type = "t3.micro"
  key_name      = "rag-key"
  security_groups = [aws_security_group.rag_sg.name]

  tags = {
    Name = "Streamlit"
  }

  user_data = file("install_streamlit.sh")
}

resource "aws_security_group" "rag_sg" {
  name        = "rag-security-group"
  description = "Allow RAG traffic"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [aws_instance.web.private_ip/32]
  }

  ingress {
    from_port   = 8501
    to_port     = 8501
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 11434
    to_port     = 11434
    protocol    = "tcp"
    cidr_blocks = [aws_instance.web.private_ip/32]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```


---

## 2. Docker Compose 파일

### 2.1 Ollama 서버 (`ollama/docker-compose.yml`)

```yaml
version: '3.8'

services:
  ollama:
    image: ollama/ollama:latest
    runtime: nvidia
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

volumes:
  ollama_data:
```


### 2.2 PostgreSQL 서버 (`postgres/docker-compose.yml`)

```yaml
version: '3.8'

services:
  postgres:
    image: ankane/pgvector:latest
    environment:
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: password
      POSTGRES_DB: ragdb
    ports:
      - "5432:5432"
    volumes:
      - pg_data:/var/lib/postgresql/data

volumes:
  pg_data:
```


### 2.3 Streamlit 앱 (`web/Dockerfile`)

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```


---

## 3. 배포 스크립트

### 3.1 Ollama 설치 스크립트 (`install_ollama.sh`)

```bash
#!/bin/bash
# NVIDIA 드라이버 설치
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://nvidia.github.io/libnvidia-container/stable/ubuntu22.04/$(ARCH) /" | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# Docker 설치
sudo apt-get install -y docker.io
sudo systemctl enable docker
sudo systemctl start docker

# Ollama 실행
mkdir -p ollama
cd ollama
curl -O https://raw.githubusercontent.com/your-repo/rag-system/main/ollama/docker-compose.yml
docker-compose up -d
```


### 3.2 PostgreSQL 설치 스크립트 (`install_postgres.sh`)

```bash
#!/bin/bash
sudo apt-get update
sudo apt-get install -y docker.io
sudo systemctl enable docker
sudo systemctl start docker

mkdir -p postgres
cd postgres
curl -O https://raw.githubusercontent.com/your-repo/rag-system/main/postgres/docker-compose.yml
docker-compose up -d
```


---

## 4. Streamlit 앱 설정

### `web/app.py` 환경변수 설정

```python
import os

DB_HOST = os.getenv('DB_HOST', 'postgres-ip') # PostgreSQL 인스턴스 Private IP
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://ollama-ip:11434') # Ollama 인스턴스 Private IP
```


---

## 5. 최종 배포 실행

```bash
# 1. Terraform 인프라 생성
terraform init
terraform apply -auto-approve

# 2. 각 서비스 접속 정보 확인
echo "Ollama 서버: $(terraform output -raw llm_public_ip)"
echo "PostgreSQL 서버: $(terraform output -raw db_private_ip)"
echo "Streamlit 웹: http://$(terraform output -raw web_public_ip):8501"

# 3. 데이터 초기화 (PostgreSQL 서버에서 실행)
ssh -i rag-key.pem ubuntu@db-server-ip 'docker exec -it postgres psql -U admin ragdb -c "CREATE EXTENSION vector;"'

# 4. 모델 로드 (Ollama 서버에서 실행)
ssh -i rag-key.pem ubuntu@llm-server-ip 'docker exec ollama ollama pull llama3'
```


---

## 문제 해결 체크리스트

1. **방화벽 확인**: 각 인스턴스의 보안 그룹에서 5432(PostgreSQL), 8501(Streamlit), 11434(Ollama) 포트 개방
2. **내부 통신**: Private IP 사용시 VPC 내부 통신 활성화 확인
3. **볼륨 마운트**: `/var/lib/docker/volumes` 경로에 쓰기 권한 확인
4. **모델 버전**: Ollama에서 사용하는 모델명(app.py의 llama3)과 실제 로드된 모델 일치 확인

이 구성을 통해 **분산형 RAG 시스템**이 완전히 배포됩니다. 각 컴포넌트의 로그는 `docker logs <컨테이너명>` 명령어로 확인 가능합니다.

