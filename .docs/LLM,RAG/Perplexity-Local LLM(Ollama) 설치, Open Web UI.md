<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Local LLM(Ollama) 설치하고 Open Web UI 오픈 소스 프로젝트를 fork하여 신규 화면(기능적으로 논문을 요약하는)을 추가하고자 합니다.

설치 가이드와 fork 소스를 기준으로 신규화면을 추가하는 과정을 상세하게 설명해 주세요. Svelt 언어로 신규화면을 추가 구현해 주세요

Ollama 설치 및 Open WebUI 커스터마이징을 통해 논문 요약 기능을 추가하는 과정을 단계별로 설명드리겠습니다. (현재 날짜: 2025년 5월 1일 기준 최신 방법)

## 1. Ollama 설치 및 모델 설정

**Windows 환경 기준 설치 단계**:

1. [Ollama 공식 사이트](https://ollama.com/download)에서 Windows 설치 파일 다운로드[^1_1][^1_14]
2. 설치 완료 후 환경변수 설정:
    - 시스템 속성 > 환경 변수 > 사용자 변수 추가
    - `OLLAMA_MODELS` 변수에 모델 저장 경로 지정(예: `D:\Ollama\Models`)[^1_1]
3. 관리자 권한 PowerShell에서 모델 설치:

```bash
ollama pull llama3  # 최신 메타 모델
ollama pull mistral # 고성능 요약 특화 모델[^1_14]
```


## 2. Open WebUI 포크 및 개발 환경 설정

**리포지토리 포크 및 클론**:

```bash
git clone https://github.com/<your-username>/open-webui.git
cd open-webui
npm install
uv pip install -r requirements.txt[^1_3][^1_11]
```


## 3. 신규 논문 요약 화면 추가

**파일 구조 생성**:

```
src/
└─ routes/
   └─ summary/
      ├─ +page.svelte    # 화면 컴포넌트
      └─ +page.server.ts # 서버 측 처리[^1_9]
```

**요약 기능 구현 코드 (src/routes/summary/+page.svelte)**:

```svelte
<script lang="ts">
  import { Ollama } from '$lib/ollama';
  let inputText = '';
  let summary = '';
  let isLoading = false;

  async function summarize() {
    isLoading = true;
    try {
      const response = await Ollama.run({
        model: 'mistral',
        prompt: `다음 논문을 3문장으로 요약해주세요: ${inputText}`
      });
      summary = response;
    } catch (error) {
      console.error('요약 실패:', error);
    }
    isLoading = false;
  }
</script>

<div class="container mx-auto p-4">
  <h1 class="text-2xl font-bold mb-4">논문 요약 시스템</h1>
  
  <textarea
    bind:value={inputText}
    class="w-full h-48 p-2 border rounded mb-4"
    placeholder="논문 내용을 붙여넣으세요..."
  />

  <button
    on:click={summarize}
    class="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
    disabled={isLoading}
  >
    {isLoading ? '요약 중...' : '요약 시작'}
  </button>

  {#if summary}
    <div class="mt-4 p-4 bg-gray-100 rounded">
      <h2 class="text-xl font-semibold mb-2">요약 결과</h2>
      <p class="whitespace-pre-wrap">{summary}</p>
    </div>
  {/if}
</div>
```


## 4. 라우팅 및 네비게이션 설정

1. 왼쪽 사이드바 메뉴 추가 (`src/lib/components/Sidebar.svelte`):
```svelte
<li class="mt-2">
  <a href="/summary" class="flex items-center p-2 hover:bg-gray-100 rounded">
    <Icon name="file-text" class="w-5 h-5 mr-2" />
    논문 요약
  </a>
</li>
```

2. 라우트 메타데이터 설정 (`src/routes/summary/+page.ts`):
```ts
import type { PageLoad } from './$types';

export const load: PageLoad = async () => {
  return {
    metadata: {
      title: '논문 요약',
      description: 'AI를 이용한 논문 자동 요약 시스템'
    }
  };
};
```


## 5. 개발 서버 실행 및 테스트

```bash
npm run dev
```

- `http://localhost:8080/summary` 접속 후 기능 테스트[^1_3][^1_11]


## 6. 커스텀 기능 배포

1. 변경사항 커밋:
```bash
git add .
git commit -m "Add paper summarization feature"
git push origin main
```

2. 원본 리포지토리로 PR 전송:
    - GitHub에서 `New Pull Request` 선택[^1_4]
    - 커밋 메시지에 `[Community Contribution]` 접두사 추가[^1_4]

## 주요 기술 스택

| 요소 | 기술 | 버전 |
| :-- | :-- | :-- |
| 프론트엔드 | SvelteKit | 2.5.3 |
| 백엔드 | Open WebUI | 1.8.2 |
| LLM 런타임 | Ollama | 0.6.1 |
| CSS 프레임워크 | Tailwind CSS | 3.4.1 |

이 구현체는 다음과 같은 확장 가능한 구조를 가집니다:

1. **다중 문서 처리**: PDF 업로드 기능 추가 가능[^1_5]
2. **요약 설정**: 문장 수/형식 사용자 지정 가능
3. **히스토리 관리**: 이전 요약 결과 저장 기능[^1_6]

개발 시 주의사항:

- Ollama 서버가 11434 포트에서 실행 중인지 확인
- 대용량 텍스트 처리 시 `max_tokens` 파라미터 조정 필요
- GPU 가속 사용 시 CUDA 버전 호환성 확인[^1_2][^1_11]
<span style="display:none">[^1_10][^1_12][^1_13][^1_15][^1_16][^1_17][^1_18][^1_19][^1_20][^1_21][^1_22][^1_23][^1_24][^1_25][^1_26][^1_27][^1_28][^1_29][^1_30][^1_31][^1_32][^1_33][^1_34][^1_35][^1_36][^1_37][^1_38][^1_39][^1_40][^1_41][^1_42][^1_43][^1_44][^1_45][^1_46][^1_47][^1_48][^1_49][^1_50][^1_51][^1_52][^1_53][^1_54][^1_55][^1_56][^1_57][^1_58][^1_59][^1_60][^1_61][^1_62][^1_63][^1_64][^1_65][^1_66][^1_67][^1_68][^1_69][^1_7][^1_70][^1_71][^1_72][^1_8]</span>

<div align="center">⁂</div>

[^1_1]: https://www.reddit.com/r/ollama/comments/1ibhxvm/guide_to_installing_and_locally_running_ollama/

[^1_2]: https://github.com/open-webui/open-webui

[^1_3]: https://docs.openwebui.com/getting-started/advanced-topics/development/

[^1_4]: https://docs.openwebui.com/tutorials/tips/contributing-tutorial/

[^1_5]: https://docs.openwebui.com/features/

[^1_6]: https://www.reddit.com/r/LocalLLaMA/comments/1fyaij3/open_webui_0331_adds_claudelike_artifacts/

[^1_7]: https://svelte.dev/playground/37d3539b4afb4f689fda387b471c0afb?version=5.19.0

[^1_8]: https://sveltekit.io/blog/snippets

[^1_9]: https://themesbrand.com/velzon/docs/svelte/create-new-page.html

[^1_10]: https://www.adventuresincre.com/how-to-install-llm-locally/

[^1_11]: https://docs.openwebui.com

[^1_12]: https://svelte.dev/tutorial

[^1_13]: http://practical.kr/?p=823

[^1_14]: https://www.langchain.ca/blog/step-by-step-guide-how-to-use-ollama-to-run-open-source-llm-models-locally/

[^1_15]: https://apidog.com/blog/deploy-local-ai-llms/

[^1_16]: https://cylab.be/blog/377/run-your-own-local-llm-with-ollama

[^1_17]: https://www.youtube.com/watch?v=0i2Eqjq3kvA

[^1_18]: https://www.freecodecamp.org/news/how-to-run-open-source-llms-locally-using-ollama/

[^1_19]: https://docs.github.com/articles/fork-a-repo

[^1_20]: https://graphite.dev/guides/git-fork

[^1_21]: https://www.leadergpu.com/catalog/584-open-webui-all-in-one

[^1_22]: https://github.com/cheahjs/open-webui-fork/releases

[^1_23]: https://www.reddit.com/r/opensource/comments/1af9v3u/can_i_fork_an_open_source_app_and_then_make_it/

[^1_24]: https://www.reddit.com/r/LocalLLaMA/comments/1df1zjr/if_you_havent_checked_out_the_open_webui_github/

[^1_25]: https://github.com/cheahjs/open-webui-fork/blob/dev/TROUBLESHOOTING.md

[^1_26]: https://www.freecodecamp.org/news/how-to-contribute-to-open-source-projects-as-a-beginner/

[^1_27]: https://dev.to/ajeetraina/how-to-setup-open-webui-with-ollama-and-docker-desktop-24f0

[^1_28]: https://daily.dev/blog/open-source-web-development-projects-for-beginners-a-guide

[^1_29]: https://github.com/open-webui/open-webui/discussions/3134

[^1_30]: https://www.digitalocean.com/resources/articles/how-to-contribute-to-open-source

[^1_31]: https://svelte.dev/docs/svelte/v5-migration-guide

[^1_32]: https://www.youtube.com/watch?v=lqKapMX2GAI

[^1_33]: https://prismic.io/blog/react-component-libraries

[^1_34]: https://www.reddit.com/r/OpenWebUI/comments/1gzh4kw/i_do_not_need_open_web_uis_backend_but_need_to/

[^1_35]: https://www.digitalbrainbase.com/t/lesson-5-chat-w-your-documents-in-open-webui/144

[^1_36]: https://obsidian.md/plugins?id=

[^1_37]: https://github.com/sveltejs/language-tools/issues/2096

[^1_38]: https://github.com/open-webui/open-webui/discussions/3432

[^1_39]: https://deepai.tn/glossary/ollama/how-to-increase-context-size-in-open-webui-a-step-by-step-guide/

[^1_40]: https://github.com/open-webui/open-webui

[^1_41]: https://github.com/open-webui/open-webui/discussions/6402

[^1_42]: https://docs.openwebui.com/features/workspace/knowledge/

[^1_43]: https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Frameworks_libraries/Svelte_components

[^1_44]: https://bejamas.com/hub/tutorials/building-reactive-uis-with-sveltekit-reactive-statements

[^1_45]: https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Frameworks_libraries/Svelte_getting_started

[^1_46]: https://purecode.ai/components/svelte/paper

[^1_47]: https://kitschpatrol.com/svelte-tweakpane-ui/docs/getting-started

[^1_48]: https://github.com/janosh/awesome-sveltekit

[^1_49]: https://stackoverflow.com/questions/75966183/how-to-add-documentation-to-a-svelte-component-on-hover-inside-vscode

[^1_50]: https://www.skeleton.dev/docs/quickstart

[^1_51]: https://javascript.plainenglish.io/how-to-document-svelte-components-part-2-9db50dff8f38

[^1_52]: https://svelte.dev/playground/bb0736e6fc79420a85ea10762184a1d2?version=3.35.0

[^1_53]: https://svelte.dev/docs/kit/load

[^1_54]: https://www.youtube.com/watch?v=LaQc5UWe0mE

[^1_55]: https://www.linkedin.com/pulse/setup-your-private-local-llm-system-ollama-open-webui-sam-jiang-evpvc

[^1_56]: https://debabratapruseth.com/how-to-install-and-run-your-first-local-llm-on-your-laptop/

[^1_57]: https://www.kdnuggets.com/ollama-tutorial-running-llms-locally-made-super-simple

[^1_58]: https://python.langchain.com/docs/integrations/llms/ollama/

[^1_59]: https://github.com/open-webui

[^1_60]: https://openwebui.com

[^1_61]: https://allthingsopen.org/articles/how-to-install-and-utilize-open-webui

[^1_62]: https://www.aibase.com/repos/topic/open-webui

[^1_63]: https://github.com/open-webui/open-webui/issues/8109

[^1_64]: https://github.com/open-webui/open-webui/issues/8889

[^1_65]: https://daisyui.com

[^1_66]: https://vercel.com/blog/ai-sdk-4-0

[^1_67]: https://svelte.dev/blog/runes

[^1_68]: https://news.ycombinator.com/item?id=40739982

[^1_69]: https://stackoverflow.com/questions/73268562/web-app-svelte-how-to-divide-screen-in-distinct-sections

[^1_70]: https://www.reddit.com/r/sveltejs/comments/1k8kjck/how_do_i_accomplish_this_form_screen_button_runs/

[^1_71]: https://svelte-babylon.netlify.app/docs/prebuilds/screen

[^1_72]: https://www.sveltevietnam.dev/en/blog/20231220-behind-the-screen-progressive-splashscreen


---

# Ollama LLM 모델을 설치한 후 Open Web UI를 설정하는 방법은

Ollama LLM 설치 및 Open WebUI 커스텀 설정을 위한 단계별 가이드를 설명드리겠습니다. (2025년 5월 기준 최신 방법)

## 1. Ollama 기본 설치

**Windows 환경**:

1. [Ollama 공식 다운로드 페이지](https://ollama.com/download)에서 설치 파일 실행
2. 환경 변수 설정(제어판 > 시스템 > 고급 시스템 설정):

```powershell
[환경 변수] → [새로 만들기] → OLLAMA_MODELS=D:\Ollama\Models[^2_1][^2_2]
```

3. PowerShell에서 필수 모델 설치:

```bash
ollama pull llama3-70b  # 70B 파라미터 모델
ollama pull mistral     # 고효율 요약 특화 모델[^2_9][^2_14]
```


## 2. Open WebUI 커스터마이징

**리포지토리 포크 및 설정**:

```bash
git clone https://github.com/<사용자명>/open-webui.git
cd open-webui
npm install --force  # 종속성 강제 설치[^2_3][^2_6]
```


## 3. 신규 요약 기능 구현

**파일 구조**:

```
src/
├─ routes/
│  └─ summary/
│     ├─ +page.svelte    # 프론트엔드 컴포넌트
│     └─ +page.server.ts # 백엔드 처리[^2_8][^2_10]
```

**요약 로직 구현 (src/routes/summary/+page.server.ts)**:

```typescript
import { Ollama } from 'ollama';
import type { RequestHandler } from './$types';

export const POST: RequestHandler = async ({ request }) => {
  const { text } = await request.json();
  
  const ollama = new Ollama({ host: 'http://localhost:11434' });
  const response = await ollama.generate({
    model: 'mistral',
    prompt: `3문장으로 논문 요약: ${text}`,
    options: { temperature: 0.7 }
  });

  return new Response(JSON.stringify({ summary: response }));
};
```


## 4. UI 컴포넌트 연동

**프론트엔드 (src/routes/summary/+page.svelte)**:

```svelte
<script lang="ts">
  let input = '';
  let summary = '';
  let loading = false;

  async function handleSubmit() {
    loading = true;
    try {
      const res = await fetch('/summary', {
        method: 'POST',
        body: JSON.stringify({ text: input })
      });
      summary = (await res.json()).summary;
    } catch (e) {
      console.error(e);
    }
    loading = false;
  }
</script>

<main class="p-4 max-w-4xl mx-auto">
  <h1 class="text-3xl font-bold mb-6">논문 요약 시스템</h1>
  
  <textarea
    bind:value={input}
    class="w-full h-64 p-3 border rounded-lg mb-4"
    placeholder="논문 텍스트를 입력하세요..."
  />

  <button
    on:click={handleSubmit}
    class="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700"
    disabled={loading}
  >
    {loading ? '처리 중...' : '요약 실행'}
  </button>

  {#if summary}
    <div class="mt-8 p-6 bg-gray-50 rounded-lg">
      <h2 class="text-xl font-semibold mb-4">요약 결과</h2>
      <p class="whitespace-pre-wrap">{summary}</p>
    </div>
  {/if}
</main>
```


## 5. Docker 컴포즈 설정

```yaml
# docker-compose.yml
version: '3.8'
services:
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama:/root/.ollama

  webui:
    image: ghcr.io/open-webui/open-webui:main
    ports:
      - "3000:8080"
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
    depends_on:
      - ollama

volumes:
  ollama:
```


## 6. 시스템 실행 및 검증

```bash
docker-compose up -d  # 백그라운드 실행[^2_6][^2_8]
# 개발 모드 실행 시
npm run dev -- --host 0.0.0.0 --port 3000[^2_3][^2_10]
```


## 주요 문제 해결 방안

1. **CORS 오류 발생 시**:

```bash
# Ollama 서버 설정 변경
OLLAMA_ORIGINS=http://localhost:3000
```

2. **GPU 가속 활성화**:

```bash
docker run --gpus all ollama/ollama[^2_6][^2_8]
```

3. **대용량 파일 처리**:

```typescript
// svelte.config.js
export default {
  kit: {
    files: {
      maxUploadSize: 50 * 1024 * 1024 // 50MB
    }
  }
};
```


이 구현체는 다음 확장 기능을 지원합니다:

- **PDF 파서 연동**: PDF.js 통한 텍스트 추출
- **멀티 모델 선택**: 사용자 정의 모델 선택 가능
- **히스토리 관리**: IndexedDB를 활용한 로컬 저장[^2_8][^2_10]

최신 업데이트 사항 반영을 위해 공식 문서와 GitHub 이슈 트래커를 정기적으로 확인하는 것이 좋습니다[^2_3][^2_6].
<span style="display:none">[^2_11][^2_12][^2_13][^2_15][^2_16][^2_17][^2_18][^2_19][^2_20][^2_21][^2_22][^2_23][^2_24][^2_25][^2_26][^2_27][^2_28][^2_29][^2_30][^2_31][^2_32][^2_33][^2_34][^2_4][^2_5][^2_7]</span>

<div align="center">⁂</div>

[^2_1]: https://www.reddit.com/r/ollama/comments/1ibhxvm/guide_to_installing_and_locally_running_ollama/

[^2_2]: https://documentation.triplo.ai/using-triplo-ai/ollama-setup-guide-for-triplo-ai

[^2_3]: https://github.com/open-webui/open-webui

[^2_4]: https://www.hostinger.com/tutorials/ollama-gui-tutorial

[^2_5]: https://dev.to/snehalkadwe/how-to-setup-ollma-and-llm-4601

[^2_6]: https://docs.openwebui.com

[^2_7]: https://www.langchain.ca/blog/step-by-step-guide-how-to-use-ollama-to-run-open-source-llm-models-locally/

[^2_8]: https://docs.vultr.com/how-to-install-open-webui-an-opensource-web-interface-for-running-llms

[^2_9]: https://www.freecodecamp.org/news/how-to-run-open-source-llms-on-your-own-computer-using-ollama/

[^2_10]: https://www.danvega.dev/blog/ollama-web-ui

[^2_11]: https://www.adventuresincre.com/how-to-install-llm-locally/

[^2_12]: https://www.youtube.com/watch?v=3W-trR0ROUY

[^2_13]: https://python.langchain.com/docs/integrations/llms/ollama/

[^2_14]: https://www.youtube.com/watch?v=UtSSMs6ObqY

[^2_15]: https://ollama.com/download

[^2_16]: https://docs.useanything.com/setup/llm-configuration/local/ollama

[^2_17]: https://github.com/ollama/ollama

[^2_18]: https://pypi.org/project/llm-ollama/

[^2_19]: https://www.youtube.com/watch?v=wIfKRi-igQc

[^2_20]: https://community.hetzner.com/tutorials/ai-chatbot-with-ollama-and-open-webui/

[^2_21]: https://docs.openwebui.com/features/

[^2_22]: https://www.linkedin.com/pulse/setup-your-private-local-llm-system-ollama-open-webui-sam-jiang-evpvc

[^2_23]: https://www.doprax.com/tutorial/a-step-by-step-guide-for-installing-and-running-ollama-and-openwebui-locally-part-1/

[^2_24]: https://www.reddit.com/r/OpenWebUI/comments/1jqkk1k/setting_up_an_llm_for_my_company_using_ollama_and/

[^2_25]: https://pasus.tistory.com/322

[^2_26]: https://adex.ltd/deploy-deepseek-r1-llm-locally-with-ollama-and-open-webui

[^2_27]: https://www.youtube.com/watch?v=BzFafshQkWw

[^2_28]: https://www.servermania.com/kb/articles/ollama-open-webui

[^2_29]: https://www.youtube.com/watch?v=cnRz2wL8Tpo

[^2_30]: https://www.kdnuggets.com/ollama-tutorial-running-llms-locally-made-super-simple

[^2_31]: http://practical.kr/?p=823

[^2_32]: https://www.youtube.com/watch?v=VbfHAHCAYT4

[^2_33]: https://gist.github.com/milank94/bddd1ee4a441b9ed53acc009d610917b

[^2_34]: https://www.youtube.com/watch?v=0R6oXJNogtg


---

# Open Web UI를 fork한 후 새로운 기능을 추가하는 방법은

Open WebUI 프로젝트를 포크(fork)하여 커스텀 기능을 추가하는 방법을 단계별로 설명드리겠습니다. (2025년 5월 기준 최신 워크플로우)

## 1. 원본 저장소 포크 및 동기화

1. [Open WebUI GitHub](https://github.com/open-webui/open-webui)에서 **Fork** 버튼 클릭
2. 생성된 포크 저장소 클론:
```bash
git clone https://github.com/<your-username>/open-webui.git
cd open-webui
```

3. 원본 저장소를 업스트림으로 등록:
```bash
git remote add upstream https://github.com/open-webui/open-webui.git
```


## 2. 기능 개발 브랜치 생성

```bash
git checkout -b feature/paper-summarizer upstream/main
```


## 3. 신규 기능 개발 절차

### 3.1 라우트 추가

```svelte
<!-- src/routes/summary/+page.svelte -->
<script lang="ts">
  // 논문 요약 로직 구현
</script>

<div class="container">
  <h1>논문 요약 시스템</h1>
  <!-- UI 컴포넌트 구현 -->
</div>
```


### 3.2 서버 사이드 처리

```typescript
// src/routes/summary/+page.server.ts
export const actions = {
  default: async ({ request }) => {
    const formData = await request.formData();
    const paperText = formData.get('text');
    
    // Ollama API 연동
    const summary = await ollama.generate({
      model: 'mistral',
      prompt: `Summarize this paper: ${paperText}`
    });
    
    return { summary };
  }
};
```


## 4. 변경사항 병합 및 PR 전송

1. 커밋 생성:
```bash
git add .
git commit -m "feat: Add paper summarization feature"
```

2. 포크 저장소에 푸시:
```bash
git push origin feature/paper-summarizer
```

3. GitHub에서 **Pull Request** 생성:
    - Base repository: `open-webui/open-webui`
    - Head repository: `<your-username>/open-webui`
    - 비교 브랜치: `main ← feature/paper-summarizer`

## 5. PR 템플릿 작성 예시

```markdown
## 변경 사항 요약
- 새로운 논문 요약 기능 추가
- SvelteKit 기반 라우트 구현
- Mistral 모델 연동

## 테스트 방법
1. `/summary` 경로 접속
2. 논문 텍스트 입력 후 요약 실행
3. 3문장 요약 결과 확인

## 관련 이슈
Resolves #123
```


## 주요 주의사항

1. **코드 컨벤션 준수**: 프로젝트의 ESLint/Prettier 규칙 적용
2. **의존성 관리**: `package.json` 변경 시 원본 저장소와 충돌 확인
3. **테스트 커버리지**: 신규 기능에 대한 Jest 테스트 케이스 작성
4. **문서 업데이트**: `docs/` 디렉토리에 사용법 문서 추가

## 문제 해결 전략

| 문제 유형 | 해결 방법 |
| :-- | :-- |
| 병합 충돌 | `git fetch upstream` → `git rebase upstream/main` |
| CI 실패 | 로컬에서 `npm run test:ci` 실행 후 에러 분석 |
| 리뷰 코멘트 | GitHub의 `Resolve conversation` 기능 활용 |

이 방법론은 오픈소스 컨트리뷰션 워크플로우를 준수하며[^3_1][^3_5], 기능 개발부터 메인 브랜치 병합까지 전체 사이클을 관리할 수 있습니다. 실제 구현 시 프로젝트의 커밋 메시지 컨벤션과 PR 가이드라인을 반드시 확인해야 합니다[^3_6][^3_9].
<span style="display:none">[^3_2][^3_3][^3_4][^3_7][^3_8]</span>

<div align="center">⁂</div>

[^3_1]: https://seungwubaek.github.io/tools/git/contributing_using_pull_request/

[^3_2]: https://dusanbaek.tistory.com/97

[^3_3]: https://toyourlight.tistory.com/125

[^3_4]: https://velog.io/@cheshire0105/누군가-내가-작성한-Pull-Request에-댓글을-달았다

[^3_5]: https://poalim.tistory.com/46

[^3_6]: https://kubernetes.io/ko/docs/contribute/new-content/open-a-pr/

[^3_7]: https://velog.io/@yun505/RealCoding1

[^3_8]: https://developer.chrome.com/blog/whats-new-css-ui-2023

[^3_9]: https://gdsc-seoultech.github.io/posts/3rd_term/seminar/2023-09-21-git_session/


---

# Docker나 Kubernetes를 사용하여 Open Web UI를 설치하는 방법은

Docker와 Kubernetes를 활용한 Open WebUI 설치 방법을 환경별로 상세히 설명드리겠습니다. (2025년 5월 기준 최신 방식)

## Docker 기반 설치

### 기본 설치 절차

```bash
# 최신 이미지 다운로드
docker pull ghcr.io/open-webui/open-webui:main

# 컨테이너 실행 (기본 설정)
docker run -d \
  -p 3000:8080 \
  -v openwebui-data:/app/backend/data \
  --name open-webui \
  --restart always \
  ghcr.io/open-webui/open-webui:main[^4_1][^4_3][^4_5]
```


### 고급 옵션

**GPU 가속 활성화(NVIDIA)**

```bash
docker run -d \
  --gpus all \
  -p 3000:8080 \
  -v openwebui-data:/app/backend/data \
  --name open-webui-gpu \
  ghcr.io/open-webui/open-webui:cuda[^4_3][^4_5]
```

**Docker Compose 구성**

```yaml
version: '3.8'
services:
  webui:
    image: ghcr.io/open-webui/open-webui:main
    ports:
      - "3000:8080"
    volumes:
      - openwebui-data:/app/backend/data
volumes:
  openwebui-data:[^4_2][^4_5]
```

실행 명령: `docker compose up -d`

## Kubernetes 배포

### 전제 조건

- Docker Desktop 설치 및 Kubernetes 활성화
- kubectl CLI 도구 설치
- Helm 차트(선택사항)


### 단계별 배포

1. 네임스페이스 생성
```bash
kubectl create namespace ollama-webui
```

2. 배포 매니페스트 적용
```yaml
# ollama-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ollama
  namespace: ollama-webui
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ollama
  template:
    metadata:
      labels:
        app: ollama
    spec:
      containers:
      - name: ollama
        image: ollama/ollama:latest
        ports:
        - containerPort: 11434
---
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: svc-open-webui
  namespace: ollama-webui
spec:
  selector:
    app: open-webui
  ports:
    - protocol: TCP
      port: 8080
      targetPort: 8080[^4_4]
```

3. 서비스 접근 설정
```bash
kubectl port-forward svc/svc-open-webui 8080:8080 -n ollama-webui
```

접속 주소: `http://localhost:8080`

## 주요 설정 옵션

| 환경 변수 | 설명 | 기본값 |
| :-- | :-- | :-- |
| OLLAMA_BASE_URL | Ollama 서버 URL | http://ollama:11434 |
| WEBUI_SECRET_KEY | 세션 암호화 키 | 랜덤 생성 |
| DISABLE_SIGNUP | 사용자 가입 기능 비활성화 | false |

## 문제 해결 팁

1. **컨테이너 실행 오류 시**
    - 볼륨 권한 확인: `chmod 777 /var/lib/docker/volumes`
    - 포트 충돌 방지: `netstat -tuln | grep 3000`[^4_1][^4_3]
2. **GPU 관련 이슈**
    - NVIDIA 드라이버 버전 확인: `nvidia-smi`
    - CUDA 호환성 점검: `nvcc --version`[^4_3][^4_5]
3. **Kubernetes 네트워크 문제**
    - 서비스 디스커버리 확인: `kubectl get endpoints -n ollama-webui`
    - 인그레스 컨트롤러 설치 여부 확인[^4_4]

이 가이드는 공식 문서와 커뮤니티 베스트 프랙티스를 반영했습니다. 실제 환경에 맞게 포트 번호와 리소스 할당량을 조정해야 합니다[^4_1][^4_2][^4_3][^4_4][^4_5].
<span style="display:none">[^4_10][^4_11][^4_12][^4_13][^4_14][^4_15][^4_16][^4_17][^4_18][^4_19][^4_20][^4_21][^4_22][^4_23][^4_24][^4_25][^4_26][^4_27][^4_28][^4_29][^4_30][^4_31][^4_32][^4_33][^4_34][^4_35][^4_36][^4_37][^4_6][^4_7][^4_8][^4_9]</span>

<div align="center">⁂</div>

[^4_1]: https://hyunicecream.tistory.com/125

[^4_2]: https://docs.openwebui.com/getting-started/quick-start/

[^4_3]: https://chalchichi.tistory.com/121

[^4_4]: https://collabnix.com/running-ollama-and-open-webui-in-a-kubernetes-cluster/

[^4_5]: https://digitalbourgeois.tistory.com/685

[^4_6]: https://www.archy.net/setting-up-ollama-with-open-webui-a-docker-compose-guide/

[^4_7]: https://www.youtube.com/watch?v=d6Su3Nmv7-8

[^4_8]: https://boksup.tistory.com/97

[^4_9]: https://geshan.com.np/blog/2025/02/ollama-docker-compose/

[^4_10]: https://docs.vultr.com/how-to-install-open-webui-an-opensource-web-interface-for-running-llms

[^4_11]: https://techjs.tistory.com/6

[^4_12]: https://dev.to/ajeetraina/how-to-setup-open-webui-with-ollama-and-docker-desktop-24f0

[^4_13]: https://docs.openwebui.com/tutorials/docker-install/

[^4_14]: https://hyunicecream.tistory.com/136

[^4_15]: https://github.com/open-webui/open-webui/blob/main/docker-compose.yaml

[^4_16]: https://github.com/open-webui/open-webui

[^4_17]: https://www.youtube.com/watch?v=lTOhY-RuKrI

[^4_18]: https://github.com/ajeetraina/ollama-openwebui-kubernetes

[^4_19]: https://docs.openwebui.com/getting-started/quick-start/

[^4_20]: https://discuss.pytorch.kr/t/open-webui-local-llm-ai/5964

[^4_21]: https://kubito.dev/posts/deploy-open-webui-kubernetes-argocd-helm-openrouter/

[^4_22]: https://mgujob.tistory.com/48

[^4_23]: https://kubernetes.io/docs/tasks/access-application-cluster/web-ui-dashboard/

[^4_24]: https://guide-to-devops.github.io/blog/ollama와-Open-WebUI-로컬-배포

[^4_25]: https://github.com/open-webui/open-webui/blob/main/INSTALLATION.md

[^4_26]: https://dewble.tistory.com/entry/install-kubernetes-web-ui-dashboard

[^4_27]: https://anakinfoxe.com/blog/install-open-webui-on-k8s-and-access-from-anywhere/

[^4_28]: https://docs.openwebui.com/tutorials/deployment/

[^4_29]: https://gimlet.io/blog/how-to-use-nvidia-gpu-with-kubernetes

[^4_30]: https://digitalbourgeois.tistory.com/685

[^4_31]: https://blackonyxkr.tistory.com/376

[^4_32]: https://velog.io/@nonz/Docker-Ollama-Open-WebUI-Gemma3

[^4_33]: https://www.youtube.com/watch?v=Qz5WWJ9v-6A

[^4_34]: https://blog.oriang.net/69

[^4_35]: https://devocean.sk.com/blog/techBoardDetail.do?ID=167177\&boardType=techBlog

[^4_36]: https://hackerpark.tistory.com/entry/Kubernetes-쿠버네티스-대시보드-OpenLens-설치-k8s-dashboard-openlens-install

[^4_37]: https://paulsmediaset.com/meta의-라마-3-1-llama-3-1을-open-webui로-쉽게-실행하기/


---

# Docker Compose를 사용하여 Open Web UI를 설치하는 방법은

Docker Compose를 사용한 Open WebUI 설치 방법을 단계별로 설명드리겠습니다. (2025년 5월 기준 최신 버전)

## 1. 필수 조건

- Docker Engine 24.0+
- Docker Compose 2.20+
- 4GB 이상의 RAM(권장)
- NVIDIA GPU 사용 시 CUDA 12.2+ 설치[^5_3][^5_6]


## 2. 설치 절차

**docker-compose.yml 파일 생성**:

```yaml
version: '3.8'
services:
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1  # GPU 개수 지정[^5_6][^5_8]

  webui:
    image: ghcr.io/open-webui/open-webui:main
    ports:
      - "3000:8080"
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
    volumes:
      - webui_data:/app/backend/data
    depends_on:
      - ollama

volumes:
  ollama_data:
  webui_data:
```

**실행 명령**:

```bash
docker compose up -d
```


## 3. 접속 및 확인

- 웹 브라우저에서 `http://localhost:3000` 접속
- 초기 설정 시 관리자 계정 생성[^5_3][^5_7]


## 4. 고급 설정 옵션

**GPU 가속 활성화**:

```yaml
# docker-compose.yml 수정
services:
  webui:
    image: ghcr.io/open-webui/open-webui:cuda  # CUDA 버전 이미지[^5_6]
```

**환경 변수 추가**:

```yaml
environment:
  - WEBUI_SECRET_KEY=mysecurekey123
  - DISABLE_SIGNUP=true  # 회원가입 비활성화[^5_4][^5_7]
```


## 5. 관리 명령어

| 기능 | 명령어 |
| :-- | :-- |
| 서비스 중지 | `docker compose down` |
| 로그 확인 | `docker compose logs -f webui` |
| 볼륨 삭제 | `docker volume prune` |

## 문제 해결 팁

1. **포트 충돌 발생 시**:

```bash
netstat -tuln | grep 3000  # 사용 중인 포트 확인
```

2. **볼륨 권한 오류**:

```bash
sudo chmod 777 /var/lib/docker/volumes
```

3. **GPU 인식 실패**:

```bash
nvidia-smi  # GPU 상태 확인
docker compose build  # 이미지 재빌드[^5_6]
```


이 방법은 공식 문서와 커뮤니티 베스트 프랙티스를 기반으로 한 최신 설치 방안입니다. 실제 환경에 맞게 포트 번호와 리소스 할당량을 조정해야 합니다[^5_1][^5_5][^5_7].
<span style="display:none">[^5_10][^5_2][^5_9]</span>

<div align="center">⁂</div>

[^5_1]: https://guide-to-devops.github.io/blog/ollama와-Open-WebUI-로컬-배포

[^5_2]: https://pasus.tistory.com/322

[^5_3]: https://hyunicecream.tistory.com/125

[^5_4]: https://changsroad.tistory.com/502

[^5_5]: https://www.lainyzine.com/ko/article/building-llm-web-service-with-open-webui

[^5_6]: https://make1solve.tistory.com/entry/Self-Hosted-GPT-Ollama-Open-WebUI

[^5_7]: https://chalchichi.tistory.com/121

[^5_8]: https://blog.oriang.net/69

[^5_9]: https://www.alibabacloud.com/blog/601700

[^5_10]: https://www.ownsoft.xyz/2019/03/docker-compose-ui.html


---

# 추가된 신규화면을 포함하여 Docker Compose, Kubernetes로 빌드 및 설치하는 방법은

신규 논문 요약 기능이 추가된 Open WebUI를 Docker Compose 및 Kubernetes로 배포하는 방법을 단계별로 설명드리겠습니다. (2025년 5월 기준 최신 배포 방식)

## Docker Compose 배포

### 1. 사용자 정의 이미지 빌드

```bash
git clone https://github.com/<your-username>/open-webui.git
cd open-webui
docker build -t custom-webui:latest .
```


### 2. docker-compose.yml 구성

```yaml
version: '3.8'
services:
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1

  webui:
    image: custom-webui:latest  # 커스텀 빌드 이미지
    ports:
      - "3000:8080"
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
    volumes:
      - webui_data:/app/backend/data
    depends_on:
      - ollama

volumes:
  ollama_data:
  webui_data:
```


### 3. 서비스 실행

```bash
docker compose up -d
```


## Kubernetes 배포

### 1. Deployment 매니페스트

```yaml
# ollama-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ollama
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ollama
  template:
    metadata:
      labels:
        app: ollama
    spec:
      containers:
      - name: ollama
        image: ollama/ollama:latest
        ports:
        - containerPort: 11434
        volumeMounts:
        - name: ollama-storage
          mountPath: /root/.ollama
      volumes:
      - name: ollama-storage
        persistentVolumeClaim:
          claimName: ollama-pvc

# webui-deployment.yaml 
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webui
spec:
  replicas: 1
  selector:
    matchLabels:
      app: webui
  template:
    metadata:
      labels:
        app: webui
    spec:
      containers:
      - name: webui
        image: custom-webui:latest
        ports:
        - containerPort: 8080
        env:
        - name: OLLAMA_BASE_URL
          value: "http://ollama:11434"
```


### 2. 서비스 노출 설정

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: ollama-svc
spec:
  selector:
    app: ollama
  ports:
    - protocol: TCP
      port: 11434
      targetPort: 11434

---
apiVersion: v1
kind: Service
metadata:
  name: webui-svc
spec:
  type: LoadBalancer
  selector:
    app: webui
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8080
```


## 주요 기능 검증

1. **신규 기능 접근**:

```bash
curl http://localhost:3000/summary
```

2. **요약 기능 테스트**:

```bash
# 테스트 요청 예시
curl -X POST -H "Content-Type: application/json" \
-d '{"text":"논문 본문 내용..."}' \
http://localhost:3000/api/summary
```


## 업데이트 전략

| 환경 | 업데이트 방법 | 데이터 보존 방법 |
| :-- | :-- | :-- |
| Docker | `docker compose pull && up -d` | 볼륨 마운트 유지 |
| Kubernetes | `kubectl rollout restart deployment` | PVC(Persistent Volume Claim) |

## 문제 해결 체크리스트

1. **GPU 리소스 할당 실패 시**

```bash
kubectl describe nodes | grep -i gpu  # GPU 노드 확인
```

2. **이미지 빌드 오류 발생 시**

```bash
docker build --no-cache -t custom-webui:latest .
```

3. **API 연결 오류**

```bash
kubectl port-forward svc/ollama-svc 11434:11434  # 포트 포워딩 테스트
```


이 구성은 확장 가능한 아키텍처를 제공하며, 신규 기능 추가 시 다음 요소들을 고려해야 합니다:

1. **의존성 관리**: `package.json` 변경 시 이미지 재빌드 필요
2. **환경 변수**: `.env` 파일을 통한 설정 관리
3. **로깅 시스템**: EFK 스택(Elasticsearch+Fluentd+Kibana) 연동 가능
<span style="display:none">[^6_1][^6_10][^6_11][^6_12][^6_13][^6_14][^6_15][^6_16][^6_17][^6_18][^6_19][^6_2][^6_20][^6_21][^6_22][^6_23][^6_24][^6_25][^6_26][^6_27][^6_28][^6_29][^6_3][^6_30][^6_31][^6_32][^6_33][^6_34][^6_35][^6_36][^6_37][^6_4][^6_5][^6_6][^6_7][^6_8][^6_9]</span>

<div align="center">⁂</div>

[^6_1]: https://docs.openwebui.com/getting-started/quick-start/

[^6_2]: https://dev.to/ajeetraina/how-to-setup-open-webui-with-ollama-and-docker-desktop-24f0

[^6_3]: https://docs.openwebui.com/features/

[^6_4]: https://github.com/open-webui/open-webui

[^6_5]: https://geshan.com.np/blog/2025/02/ollama-docker-compose/

[^6_6]: https://docs.openwebui.com

[^6_7]: https://www.archy.net/setting-up-ollama-with-open-webui-a-docker-compose-guide/

[^6_8]: https://github.com/open-webui/open-webui/blob/main/INSTALLATION.md

[^6_9]: https://techcommunity.microsoft.com/blog/educatordeveloperblog/deploy-open-web-ui-on-azure-vm-via-docker-a-step-by-step-guide-with-custom-domai/4387717

[^6_10]: https://opensearch.org/docs/2.18/install-and-configure/install-opensearch/docker/

[^6_11]: https://mydeveloperplanet.com/2025/02/05/explore-open-webui-your-offline-ai-interface/

[^6_12]: https://www.restack.io/p/ollama-answer-open-webui-docker-compose-cat-ai

[^6_13]: https://docs.openwebui.com

[^6_14]: https://www.jetson-ai-lab.com/tutorial_openwebui.html

[^6_15]: https://github.com/psyray/open-webui-docker

[^6_16]: https://code.ovgu.de/usc/von-github/open-webui/-/blob/v0.1.102/README.md

[^6_17]: https://hacking-and-security.cc/beginners-guide-to-setup-a-local-chatgpt-alternative-using-open-webui-and-ollama/

[^6_18]: https://docs.openappsec.io/getting-started/start-with-docker/deploy-with-docker-compose-beta

[^6_19]: https://www.youtube.com/watch?v=FHTYrMtLkmQ

[^6_20]: https://github.com/open-webui/open-webui/discussions/493

[^6_21]: https://portkey.ai/blog/openwebui-vs-librechat/

[^6_22]: https://docs.openwebui.com/tutorials/tips/contributing-tutorial/

[^6_23]: https://www.servermania.com/kb/articles/ollama-open-webui

[^6_24]: https://spacelift.io/blog/kubernetes-dashboard

[^6_25]: https://railway.com/template/Hez7Hu

[^6_26]: https://allthingsopen.org/articles/how-to-install-and-utilize-open-webui

[^6_27]: https://docs.digitalocean.com/products/marketplace/catalog/open-webui/

[^6_28]: https://blogops.mixinet.net/posts/testing_deepseek_with_ollama_and_open_webui/

[^6_29]: https://docs.gitlab.com/user/project/merge_requests/creating_merge_requests/

[^6_30]: https://www.reddit.com/r/kubernetes/comments/1h1pgxv/new_lens_is_broken_is_opensource_fork_viable/

[^6_31]: https://code.visualstudio.com/docs/sourcecontrol/github

[^6_32]: https://docs.openwebui.com/getting-started/

[^6_33]: https://github.com/deepset-ai/hayhooks-open-webui-docker-compose

[^6_34]: https://www.youtube.com/watch?v=JJ_0-pAOIEk

[^6_35]: https://kubernetes.io/docs/tasks/access-application-cluster/web-ui-dashboard/

[^6_36]: https://kubernetes.io/docs/contribute/new-content/open-a-pr/

[^6_37]: https://docs.vultr.com/how-to-install-open-webui-an-opensource-web-interface-for-running-llms

