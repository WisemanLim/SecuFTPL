"use client";
// 데이터셋 — 절차: ①사용용도 → ②수집 채널 선택 → ③수집 → ④증강 (PRD §7.3·§7.4)
import { useState } from "react";
import { api, fmt } from "@/lib/api";
import { buildTemplate } from "@/lib/templates";

const TASK_TYPES = [
  ["alert_triage", "SOC 경보 분류·요약"],
  ["cti_extraction", "CTI/ATT&CK 구조화"],
  ["vuln_triage", "취약점 우선순위화"],
  ["policy_qa", "보안 정책 질의응답"],
  ["safety_refusal", "안전 거부"],
] as const;

const CHANNELS = [
  ["direct", "직접 입력 (JSONL 템플릿)"],
  ["files", "파일 업로드 — JSONL/JSON·PDF/DOCX/TXT/MD/HTML (멀티)"],
  ["userdir", "사용자 디렉토리 — 보고서 폴더 통째로 선택"],
  ["url", "인터넷(URL) — 화이트리스트 도메인"],
] as const;
type Channel = (typeof CHANNELS)[number][0];

type Suggestion = { keyword: string; frequency: number; candidates: string[] };

export default function DatasetsPage() {
  // ① 사용용도
  const [taskType, setTaskType] = useState("alert_triage");
  // ② 채널
  const [channel, setChannel] = useState<Channel>("direct");
  // ③ 채널별 입력
  const [jsonl, setJsonl] = useState(() => buildTemplate("alert_triage"));
  const [autoFill, setAutoFill] = useState(true);
  const [files, setFiles] = useState<File[]>([]);
  const [srcFormat, setSrcFormat] = useState("canonical");
  const [url, setUrl] = useState("");
  // ④ 증강
  const [subs, setSubs] = useState('{"아파치":"nginx"}');
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  // ⑤ 다운로드 (F13)
  const [expFormat, setExpFormat] = useState("canonical");
  const [expState, setExpState] = useState("approved");
  const [expVersion, setExpVersion] = useState("");
  const [withManifest, setWithManifest] = useState(true);
  const [out, setOut] = useState("-");

  const changeTask = (t: string) => {
    setTaskType(t);
    if (autoFill || !jsonl.trim()) setJsonl(buildTemplate(t));
  };
  const run = (fn: () => Promise<unknown>) => async () => {
    try { setOut(fmt(await fn())); } catch (e) { setOut(String(e)); }
  };
  const parse = () => {
    const records = jsonl.split("\n").filter((l) => l.trim()).map((l) => {
      const r = JSON.parse(l);
      r.metadata ??= {};
      if (!r.metadata.task_type) r.metadata.task_type = taskType;
      return r;
    });
    if (records.length === 0) throw new Error("수집할 레코드가 없습니다 — 템플릿 채우기 또는 JSONL 입력 필요");
    return records;
  };
  const uploadFiles = async () => {
    const form = new FormData();
    for (const f of files) form.append("files", f);
    form.append("source_format", srcFormat);
    form.append("task_type", taskType);
    const res = await fetch("/api/v1/records/upload", { method: "POST", body: form });
    const data = await res.json();
    if (!res.ok) throw new Error(`${res.status} ${JSON.stringify(data)}`);
    return data;
  };

  return (
    <>
      <section className="panel">
        <h2>① 사용용도 (task_type)</h2>
        <div className="row">
          <select value={taskType} onChange={(e) => changeTask(e.target.value)} aria-label="task type">
            {TASK_TYPES.map(([v, label]) => <option key={v} value={v}>{v} — {label}</option>)}
          </select>
          <span className="pill">문서 수집 시 이 용도의 지시 프레임으로 주석 대기 레코드 생성</span>
        </div>
      </section>

      <section className="panel">
        <h2>② 수집 채널 선택</h2>
        <div className="row" role="radiogroup" aria-label="수집 채널">
          {CHANNELS.map(([v, label]) => (
            <label key={v} className="pill" style={{ cursor: "pointer",
              background: channel === v ? "var(--acc-bg)" : undefined,
              color: channel === v ? "var(--acc-strong)" : undefined }}>
              <input type="radio" name="channel" value={v} checked={channel === v}
                     onChange={() => setChannel(v)} style={{ marginRight: 6 }} />
              {label}
            </label>
          ))}
        </div>
      </section>

      <section className="panel">
        <h2>③ 데이터 수집</h2>
        {channel === "direct" && (
          <>
            <div className="row">
              <button className="ghost" onClick={() => { setJsonl(buildTemplate(taskType)); setAutoFill(true); }}>
                템플릿 다시 채우기
              </button>
              <select value={srcFormat} onChange={(e) => setSrcFormat(e.target.value)} aria-label="포맷">
                {["canonical", "alpaca", "sharegpt", "openai-chat"].map((f) => <option key={f}>{f}</option>)}
              </select>
            </div>
            <textarea value={jsonl} aria-label="jsonl"
              onChange={(e) => { setJsonl(e.target.value); setAutoFill(false); }} />
            <div className="row">
              <button className="ghost" onClick={run(() => api("POST", "/api/v1/datasets/validate", { records: parse() }))}>검증만</button>
              <button onClick={run(() => api("POST", "/api/v1/records/ingest", { records: parse() }))}>수집(ingest)</button>
              <button className="ghost" onClick={run(() => api("POST", "/api/v1/datasets/convert",
                { items: jsonl.split("\n").filter((l) => l.trim()).map((l) => JSON.parse(l)),
                  source: srcFormat, target: "canonical" }))}>포맷 변환 미리보기</button>
            </div>
          </>
        )}
        {channel === "files" && (
          <div className="row">
            <input type="file" multiple accept=".jsonl,.json,.pdf,.docx,.txt,.md,.html" aria-label="파일 선택"
                   onChange={(e) => setFiles(Array.from(e.target.files ?? []))} />
            <select value={srcFormat} onChange={(e) => setSrcFormat(e.target.value)} aria-label="정형 포맷">
              {["canonical", "alpaca", "sharegpt", "openai-chat"].map((f) => <option key={f}>{f}</option>)}
            </select>
            <button disabled={files.length === 0} onClick={run(uploadFiles)}>수집 실행 ({files.length}개)</button>
            <span className="pill">PDF/DOCX 등 문서 = 텍스트 추출 → 검수 단계에서 정답 작성</span>
          </div>
        )}
        {channel === "userdir" && (
          <div className="row">
            {/* 사용자 디렉토리 선택 — 브라우저 webkitdirectory (서버 경로 아님) */}
            <input type="file" aria-label="디렉토리 선택"
                   // @ts-expect-error 비표준(전 브라우저 지원) 디렉토리 선택 속성
                   webkitdirectory="" directory="" multiple
                   onChange={(e) => setFiles(Array.from(e.target.files ?? []))} />
            <button disabled={files.length === 0} onClick={run(uploadFiles)}>
              디렉토리 수집 ({files.length}개 파일)
            </button>
            <span className="pill">보고서 폴더 선택 → 하위 파일 일괄 수집 (지원 확장자만 처리)</span>
          </div>
        )}
        {channel === "url" && (
          <div className="row">
            <input type="text" value={url} onChange={(e) => setUrl(e.target.value)}
                   placeholder="https://... (화이트리스트 도메인만)" style={{ minWidth: 380 }} aria-label="수집 URL" />
            <button disabled={!url.trim()} onClick={run(() => api("POST", "/api/v1/records/collect/url",
              { url, source_format: srcFormat, task_type: taskType }))}>수집 실행</button>
            <span className="pill">수집 정의: JSON/JSONL=레코드 · HTML/TXT/MD=본문 추출→주석 대기. T3_untrusted 태깅</span>
          </div>
        )}
      </section>

      <section className="panel">
        <h2>④ 증강 (검수 승인 후)</h2>
        <div className="row">
          <button className="ghost" onClick={run(async () => {
            const data = await api<{ suggestions: Suggestion[] }>("GET", "/api/v1/records/augment/suggestions");
            setSuggestions(data.suggestions);
            return data;
          })}>치환 후보 자동 추천</button>
          {suggestions.map((s) => (
            <button key={s.keyword} className="ghost" title={`빈도 ${s.frequency}`}
                    onClick={() => setSubs(JSON.stringify({ [s.keyword]: s.candidates[0] }))}>
              {s.keyword}→{s.candidates[0]} ({s.frequency})
            </button>
          ))}
        </div>
        <div className="row">
          <input type="text" value={subs} onChange={(e) => setSubs(e.target.value)}
                 style={{ minWidth: 320 }} aria-label="치환 사전 JSON" />
          <button onClick={run(() => api("POST", "/api/v1/records/augment",
            { method: "keyword", substitutions: JSON.parse(subs) }))}>키워드 치환 증강</button>
          <button className="ghost" onClick={run(() => api("POST", "/api/v1/records/augment",
            { method: "backtranslate" }))}>역번역 증강 (ko→en→ko, Ollama)</button>
          <button className="ghost" onClick={run(() => api("POST", "/api/v1/records/augment",
            { method: "paraphrase" }))}>패러프레이즈 증강 (LLM 재구성, Ollama)</button>
        </div>
        <p style={{ color: "var(--sub)", fontSize: 12.5, margin: "4px 0 0" }}>
          승인(approved) 원본만 대상. 증강본은 검수 큐 재편입, CVE/ATT&CK/CWE 식별자 불변.
          역번역·패러프레이즈는 Ollama 기동 필요(<code>OLLAMA_BASE_URL</code>).
        </p>
      </section>
      <section className="panel">
        <h2>⑤ 데이터셋 다운로드 (F13 — 출처 manifest 포함)</h2>
        <div className="row">
          <select value={expFormat} onChange={(e) => setExpFormat(e.target.value)} aria-label="export 포맷">
            {["canonical", "alpaca", "sharegpt", "openai-chat", "dpo-pairs", "eval-set"]
              .map((f) => <option key={f}>{f}</option>)}
          </select>
          <select value={expState} onChange={(e) => setExpState(e.target.value)} aria-label="검수 상태">
            {["approved", "pending", "rejected", "all"].map((s) => <option key={s}>{s}</option>)}
          </select>
          <input type="text" value={expVersion} onChange={(e) => setExpVersion(e.target.value)}
                 placeholder="dataset_version (미지정=전체)" aria-label="dataset version" />
          <label className="pill" style={{ cursor: "pointer" }}>
            <input type="checkbox" checked={withManifest} onChange={(e) => setWithManifest(e.target.checked)}
                   style={{ marginRight: 6 }} />
            manifest 동봉 (zip — 출처 집계·sha256)
          </label>
        </div>
        <div className="row">
          <button onClick={() => {
            const q = new URLSearchParams({ format: expFormat, review_state: expState,
              with_manifest: String(withManifest) });
            if (expVersion.trim()) q.set("dataset_version", expVersion.trim());
            window.open(`/api/v1/datasets/export?${q}`, "_blank");
          }}>다운로드</button>
          <button className="ghost" onClick={run(() => {
            const q = new URLSearchParams({ format: expFormat, review_state: expState });
            if (expVersion.trim()) q.set("dataset_version", expVersion.trim());
            return api("GET", `/api/v1/datasets/export/manifest?${q}`);
          })}>manifest 미리보기 (출처 검증)</button>
          <button className="ghost" onClick={run(() => api("GET", "/api/v1/datasets/runs"))}>
            수집·정제 run 이력 (F15)
          </button>
        </div>
        <p style={{ color: "var(--sub)", fontSize: 12.5, margin: "4px 0 0" }}>
          문서/디렉토리 수집 결과 포함. manifest 에 출처(source_uri·license)별 집계와 파일 sha256 이
          명기되어 보안전문가 외부 검증·에어갭 반입 증빙에 사용.
        </p>
      </section>
      <pre className="out">{out}</pre>
    </>
  );
}
