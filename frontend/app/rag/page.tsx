"use client";
// RAG 추가학습·모델 업그레이드 — 절차: ①코퍼스 합성 → ②검수 큐 승인 → ③업그레이드 잡 제출 (PRD F10·§7.13)
import { useCallback, useEffect, useState } from "react";
import { api, fmt } from "@/lib/api";

const TASK_TYPES = [
  ["alert_triage", "SOC 경보 분류·요약"],
  ["cti_extraction", "CTI/ATT&CK 구조화"],
  ["vuln_triage", "취약점 우선순위화"],
  ["policy_qa", "보안 정책 질의응답"],
  ["safety_refusal", "안전 거부"],
] as const;

type Doc = { title: string; text: string };
type Model = { model_id: string; status: string };
type Job = { job_id: string; model_id: string; dataset_version: string; status: string };

export default function RagPage() {
  // 공통
  const [taskType, setTaskType] = useState("alert_triage");
  const [datasetVersion, setDatasetVersion] = useState("v0.1.0");
  const [chunkSize, setChunkSize] = useState(800);
  const [out, setOut] = useState("-");

  // ① 텍스트 코퍼스 직접 입력
  const [docTitle, setDocTitle] = useState("");
  const [docText, setDocText] = useState("");
  const [docs, setDocs] = useState<Doc[]>([]);
  const addDoc = () => {
    if (!docTitle.trim() || !docText.trim()) return;
    setDocs((prev) => [...prev, { title: docTitle.trim(), text: docText }]);
    setDocTitle(""); setDocText("");
  };
  const removeDoc = (i: number) => setDocs((prev) => prev.filter((_, idx) => idx !== i));

  // ① 파일 업로드
  const [files, setFiles] = useState<File[]>([]);

  const run = (fn: () => Promise<unknown>) => async () => {
    try { setOut(fmt(await fn())); } catch (e) { setOut(String(e)); }
  };

  const synthesizeText = async () => {
    if (docs.length === 0) throw new Error("합성할 문서가 없습니다 — 제목/본문 입력 후 '추가'");
    const res = await api("POST", "/api/v1/rag/synthesize", {
      documents: docs, task_type: taskType, dataset_version: datasetVersion, chunk_size: chunkSize,
    });
    setDocs([]);
    return res;
  };

  const synthesizeFiles = async () => {
    const form = new FormData();
    for (const f of files) form.append("files", f);
    form.append("task_type", taskType);
    form.append("dataset_version", datasetVersion);
    form.append("chunk_size", String(chunkSize));
    const res = await fetch("/api/v1/rag/upload", { method: "POST", body: form });
    const data = await res.json();
    if (!res.ok) throw new Error(`${res.status} ${JSON.stringify(data)}`);
    setFiles([]);
    return data;
  };

  // ③ 모델 업그레이드
  const [models, setModels] = useState<Model[]>([]);
  const [succeededJobs, setSucceededJobs] = useState<Job[]>([]);
  const [upModelId, setUpModelId] = useState("");
  const [upDatasetVersion, setUpDatasetVersion] = useState("v0.1.0");
  const [continualFrom, setContinualFrom] = useState("");
  const [upMaxGpu, setUpMaxGpu] = useState<number | "">("");
  const [upMaxVramGb, setUpMaxVramGb] = useState<number | "">("");

  const loadModelsAndJobs = useCallback(async () => {
    try {
      const [m, j] = await Promise.all([
        api<{ models: Model[] }>("GET", "/api/v1/models"),
        api<{ jobs: Job[] }>("GET", "/api/v1/tuning/jobs?status=succeeded"),
      ]);
      setModels(m.models);
      setSucceededJobs(j.jobs);
      if (!upModelId && m.models.length) setUpModelId(m.models[0].model_id);
    } catch (e) { setOut(String(e)); }
  }, [upModelId]);
  useEffect(() => { loadModelsAndJobs(); }, [loadModelsAndJobs]);

  const upgrade = () => api("POST", "/api/v1/rag/upgrade", {
    model_id: upModelId, dataset_version: upDatasetVersion,
    continual_from_job_id: continualFrom || undefined,
    max_gpu: upMaxGpu === "" ? undefined : upMaxGpu,
    max_vram_gb: upMaxVramGb === "" ? undefined : upMaxVramGb,
  });

  return (
    <>
      <section className="panel">
        <h2>① RAG 코퍼스 → 합성 QA <span className="pill">F10</span></h2>
        <div className="row">
          <select value={taskType} onChange={(e) => setTaskType(e.target.value)} aria-label="task type">
            {TASK_TYPES.map(([v, label]) => <option key={v} value={v}>{label}</option>)}
          </select>
          <input type="text" value={datasetVersion} onChange={(e) => setDatasetVersion(e.target.value)}
                 aria-label="dataset version" />
          <input type="number" min={200} max={4000} value={chunkSize}
                 onChange={(e) => setChunkSize(Number(e.target.value))} aria-label="chunk size" />
        </div>

        <h3 style={{ fontSize: 13.5, margin: "12px 0 4px" }}>텍스트 직접 입력</h3>
        <div className="row">
          <input type="text" placeholder="문서 제목" value={docTitle}
                 onChange={(e) => setDocTitle(e.target.value)} aria-label="document title" />
        </div>
        <textarea rows={4} placeholder="문서 본문 (청킹 후 cause/resolution 합성)"
                  value={docText} onChange={(e) => setDocText(e.target.value)}
                  style={{ width: "100%", marginTop: 6 }} aria-label="document text" />
        <div className="row" style={{ marginTop: 6 }}>
          <button className="ghost" onClick={addDoc}>문서 추가 ({docs.length})</button>
          <button disabled={docs.length === 0} onClick={run(synthesizeText)}>합성 실행 (텍스트)</button>
        </div>
        {docs.length > 0 && (
          <ul style={{ margin: "6px 0", paddingLeft: 18, fontSize: 12.5 }}>
            {docs.map((d, i) => (
              <li key={`${d.title}-${i}`}>
                {d.title} ({d.text.length}자){" "}
                <button className="ghost btn-pill" onClick={() => removeDoc(i)}>제거</button>
              </li>
            ))}
          </ul>
        )}

        <h3 style={{ fontSize: 13.5, margin: "12px 0 4px" }}>문서 파일 업로드 (PDF/DOCX/TXT/MD/HTML)</h3>
        <div className="row">
          <input type="file" multiple accept=".pdf,.docx,.txt,.md,.html" aria-label="RAG 코퍼스 파일 선택"
                 onChange={(e) => setFiles(Array.from(e.target.files ?? []))} />
          <button disabled={files.length === 0} onClick={run(synthesizeFiles)}>합성 실행 (파일 {files.length}개)</button>
        </div>
        <p style={{ color: "var(--sub)", fontSize: 12.5, margin: "6px 0 0" }}>
          합성 레코드도 정제 게이트를 통과해 검수 큐(pending)에 적재된다 — 승인은 <b>검수 큐</b> 페이지에서.
        </p>
      </section>

      <section className="panel">
        <h2>② 모델 업그레이드 (continual fine-tuning) <span className="pill">F10</span></h2>
        <div className="row">
          <select value={upModelId} onChange={(e) => setUpModelId(e.target.value)} aria-label="upgrade model">
            {models.map((m) => <option key={m.model_id} value={m.model_id}>{m.model_id} ({m.status})</option>)}
          </select>
          <input type="text" value={upDatasetVersion} onChange={(e) => setUpDatasetVersion(e.target.value)}
                 aria-label="upgrade dataset version" />
          <select value={continualFrom} onChange={(e) => setContinualFrom(e.target.value)}
                  aria-label="continual from job">
            <option value="">이어학습 기준 없음(신규)</option>
            {succeededJobs.map((j) => (
              <option key={j.job_id} value={j.job_id}>{j.job_id} ({j.model_id})</option>
            ))}
          </select>
          <input type="number" min={1} placeholder="max_gpu" style={{ width: 90 }}
                 value={upMaxGpu} onChange={(e) => setUpMaxGpu(e.target.value === "" ? "" : Number(e.target.value))}
                 aria-label="upgrade max gpu" />
          <input type="number" min={1} placeholder="max_vram_gb" style={{ width: 110 }}
                 value={upMaxVramGb} onChange={(e) => setUpMaxVramGb(e.target.value === "" ? "" : Number(e.target.value))}
                 aria-label="upgrade max vram gb" />
          <button onClick={run(upgrade)}>업그레이드 잡 제출</button>
        </div>
        <p style={{ color: "var(--sub)", fontSize: 12.5, margin: "6px 0 0" }}>
          승인 레코드가 500건 이상이어야 제출 가능(§7.5). 결과는 <b>리더보드</b>에 기존 모델과
          나란히 등재되어 업그레이드 전/후 비교가 가능하다.
        </p>
      </section>

      <pre className="out">{out}</pre>
    </>
  );
}
