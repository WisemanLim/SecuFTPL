"use client";
// 튜닝 — 모델 선택 → 잡 생성 → 플랜 → 배치 (PRD E3/E6/E7)
import { useCallback, useEffect, useState } from "react";
import { api, fmt } from "@/lib/api";

type Job = { job_id: string; model_id: string; dataset_version: string; record_count: number;
             status: string; triggered_by: string; progress_pct: number;
             current_step: number; total_steps: number; error: string | null;
             max_gpu: number; max_vram_gb: number };
type Model = { model_id: string; status: string };

export default function TuningPage() {
  const [models, setModels] = useState<Model[]>([]);
  const [modelId, setModelId] = useState("");
  const [datasetVersion, setDatasetVersion] = useState("v0.1.0");
  const [maxGpu, setMaxGpu] = useState<number | "">("");
  const [maxVramGb, setMaxVramGb] = useState<number | "">("");
  const [jobs, setJobs] = useState<Job[]>([]);
  const [out, setOut] = useState("-");

  const load = useCallback(async () => {
    try {
      const [m, j] = await Promise.all([
        api<{ models: Model[] }>("GET", "/api/v1/models"),
        api<{ jobs: Job[] }>("GET", "/api/v1/tuning/jobs"),
      ]);
      setModels(m.models);
      setJobs(j.jobs);
      if (!modelId && m.models.length) setModelId(m.models[0].model_id);
    } catch (e) { setOut(String(e)); }
  }, [modelId]);
  useEffect(() => { load(); }, [load]);

  // running 잡이 있으면 2초 주기 자동 새로고침 (신규 잡 발견용 — 다른 세션/배치가 만든 잡 포함)
  useEffect(() => {
    if (!jobs.some((j) => j.status === "running")) return;
    const t = setInterval(load, 2000);
    return () => clearInterval(t);
  }, [jobs, load]);

  // 실시간 스트리밍(WebSocket) — running 잡마다 구독해 진행률을 즉시 반영(폴링보다 저지연)
  const runningIds = jobs.filter((j) => j.status === "running").map((j) => j.job_id).join(",");
  useEffect(() => {
    if (!runningIds) return;
    const proto = window.location.protocol === "https:" ? "wss" : "ws";
    const sockets = runningIds.split(",").map((jobId) => {
      const ws = new WebSocket(`${proto}://${window.location.host}/api/v1/tuning/jobs/${jobId}/stream`);
      ws.onmessage = (ev) => {
        const msg = JSON.parse(ev.data);
        if (msg.error) return;
        setJobs((prev) => prev.map((p) => p.job_id === msg.job_id
          ? { ...p, status: msg.status, progress_pct: msg.progress_pct,
              current_step: msg.current_step, total_steps: msg.total_steps }
          : p));
        if (msg.status === "succeeded" || msg.status === "failed") load(); // adapter_uri 등 최종 반영
      };
      return ws;
    });
    return () => sockets.forEach((ws) => ws.close());
  }, [runningIds, load]);

  const run = (fn: () => Promise<unknown>) => async () => {
    try { setOut(fmt(await fn())); await load(); } catch (e) { setOut(String(e)); }
  };

  const showHistory = async (jobId: string) => {
    try {
      const ev = await api<{ events: { message: string; at: string }[] }>(
        "GET", `/api/v1/tuning/jobs/${jobId}/events`);
      setOut(`이벤트 히스토리 — ${jobId}\n` + ev.events.map((e) => `${e.at}  ${e.message}`).join("\n"));
    } catch (e) { setOut(String(e)); }
  };
  const exportModel = (jobId: string, format: "adapter" | "full") => {
    // tar.gz 다운로드 — 프록시 경유 브라우저 저장 (F11: adapter=경량 | full=merge 풀모델)
    window.location.href = `/api/v1/tuning/jobs/${jobId}/export?format=${format}`;
  };
  const showResources = async (jobId: string) => {
    try {
      const r = await api<{ limits: { max_gpu: number; max_vram_gb: number }; cpu_pct: number;
                            mem_used_pct: number; gpu_mode: string;
                            gpu_devices: { index: number; util_pct: number; vram_used_gb: number;
                                          vram_total_gb: number }[] }>(
        "GET", `/api/v1/tuning/jobs/${jobId}/resources`);
      const gpuLines = r.gpu_devices.map((d) =>
        `  GPU${d.index}: util=${d.util_pct}% vram=${d.vram_used_gb}/${d.vram_total_gb}GB`).join("\n");
      setOut(`리소스 모니터링 — ${jobId} (F9)\n`
        + `한도: max_gpu=${r.limits.max_gpu} max_vram_gb=${r.limits.max_vram_gb}\n`
        + `CPU: ${r.cpu_pct}%  MEM: ${r.mem_used_pct}%  GPU모드: ${r.gpu_mode}\n${gpuLines}`);
    } catch (e) { setOut(String(e)); }
  };
  const showExportPlan = async (jobId: string, target: "gguf" | "mlx") => {
    try {
      const r = await api<{ command: string }>(
        "GET", `/api/v1/tuning/jobs/${jobId}/export-plan?target=${target}`);
      setOut(`런타임 변환 플랜(F11, 실행 없음) — ${jobId} → ${target}\n\n${r.command}`);
    } catch (e) { setOut(String(e)); }
  };

  return (
    <>
      <section className="panel">
        <h2>튜닝 잡 생성</h2>
        <div className="row">
          <select value={modelId} onChange={(e) => setModelId(e.target.value)} aria-label="model">
            {models.map((m) => <option key={m.model_id} value={m.model_id}>{m.model_id} ({m.status})</option>)}
          </select>
          <input type="text" value={datasetVersion} onChange={(e) => setDatasetVersion(e.target.value)} aria-label="dataset version" />
          <input type="number" min={1} placeholder="max_gpu" style={{ width: 90 }}
                 value={maxGpu} onChange={(e) => setMaxGpu(e.target.value === "" ? "" : Number(e.target.value))}
                 aria-label="max gpu" />
          <input type="number" min={1} placeholder="max_vram_gb" style={{ width: 110 }}
                 value={maxVramGb} onChange={(e) => setMaxVramGb(e.target.value === "" ? "" : Number(e.target.value))}
                 aria-label="max vram gb" />
          <button onClick={run(() => api("POST", "/api/v1/tuning/jobs", {
            model_id: modelId, dataset_version: datasetVersion,
            max_gpu: maxGpu === "" ? undefined : maxGpu,
            max_vram_gb: maxVramGb === "" ? undefined : maxVramGb,
          }))}>잡 제출</button>
        </div>
        <p style={{ color: "var(--sub)", fontSize: 12.5, margin: "4px 0 0" }}>
          실학습은 GPU worker 가 플랜(YAML)으로 실행 — 여기서는 잡·플랜·상태 관리.
          리소스(max_gpu/max_vram_gb) 미입력 시 시스템 기본값 사용(F9).
        </p>
      </section>
      <section className="panel">
        <h2>야간 배치 (E6)</h2>
        <div className="row">
          <button className="ghost" onClick={run(() => api("GET", "/api/v1/batch/should-run"))}>트리거 판정</button>
          <button onClick={run(() => api("POST", "/api/v1/batch/run", {}))}>배치 실행</button>
          <button className="ghost" onClick={run(() => api("GET", "/api/v1/batch/runs"))}>배치 이력</button>
          <button className="ghost" onClick={run(async () =>
            (await api<{ command: string }>("GET", "/api/v1/batch/cron-plan")).command)}>ops cron 플랜</button>
        </div>
        <p style={{ color: "var(--sub)", fontSize: 12.5, margin: "4px 0 0" }}>
          cron 플랜은 crontab 라인만 생성 — 자동 설치 없음, ops 가 `crontab -e` 로 직접 반영.
        </p>
      </section>
      <section className="panel">
        <h2>잡 목록</h2>
        <table>
          <thead><tr><th>job_id</th><th>model</th><th>dataset</th><th>records</th><th>resources</th><th>status</th><th>by</th><th>액션</th></tr></thead>
          <tbody>
            {jobs.map((j) => {
              const cls = j.status === "succeeded" ? " ok" : j.status === "failed" ? " bad" : "";
              return (
                <tr key={j.job_id}>
                  <td>{j.job_id}</td><td>{j.model_id}</td><td>{j.dataset_version}</td>
                  <td>{j.record_count}</td>
                  <td><small style={{ color: "var(--sub)" }}>gpu={j.max_gpu} vram={j.max_vram_gb}GB</small></td>
                  <td>
                    <span className={"pill" + cls}>{j.status}</span>
                    {j.status === "running" && (
                      <div style={{ marginTop: 4 }}>
                        <div style={{ height: 6, background: "var(--line)", borderRadius: 4, overflow: "hidden", minWidth: 90 }}>
                          <div style={{ height: "100%", width: `${j.progress_pct}%`, background: "var(--acc-bright)" }} />
                        </div>
                        <small style={{ color: "var(--sub)" }}>{j.progress_pct}% ({j.current_step}/{j.total_steps})</small>
                      </div>
                    )}
                    {j.status === "failed" && j.error && (
                      <div><small style={{ color: "var(--bad)" }}>{j.error}</small></div>
                    )}
                  </td>
                  <td>{j.triggered_by}</td>
                  <td>
                    <button className="ghost btn-pill" onClick={() => showHistory(j.job_id)}>히스토리</button>{" "}
                    <button className="ghost btn-pill" onClick={() => showResources(j.job_id)}>리소스</button>{" "}
                    <button className="ghost btn-pill" onClick={run(async () =>
                      (await api<{ plan: string }>("GET", `/api/v1/tuning/jobs/${j.job_id}/plan`)).plan)}>플랜</button>{" "}
                    {j.status === "succeeded" && (
                      <>
                        <button className="btn-pill" onClick={() => exportModel(j.job_id, "adapter")}>다운로드(어댑터)</button>{" "}
                        <button className="btn-pill" onClick={() => exportModel(j.job_id, "full")}>다운로드(풀모델)</button>{" "}
                        <button className="ghost btn-pill" onClick={() => showExportPlan(j.job_id, "gguf")}>GGUF 플랜</button>{" "}
                        <button className="ghost btn-pill" onClick={() => showExportPlan(j.job_id, "mlx")}>MLX 플랜</button>
                      </>
                    )}{" "}
                    {(j.status === "queued" || j.status === "failed") && (
                      <button className="btn-pill" onClick={run(() =>
                        api("POST", `/api/v1/tuning/jobs/${j.job_id}/retry`))}>재실행</button>
                    )}{" "}
                    {j.status !== "running" && (
                      <button className="ghost btn-pill" style={{ color: "var(--bad)", borderColor: "var(--bad)" }}
                        onClick={async () => {
                          if (!window.confirm(`잡 '${j.job_id}' 삭제? (이벤트 로그 포함, 되돌릴 수 없음)`)) return;
                          try { setOut(fmt(await api("DELETE", `/api/v1/tuning/jobs/${j.job_id}`))); await load(); }
                          catch (e) { setOut(String(e)); }
                        }}>삭제</button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </section>
      <pre className="out">{out}</pre>
    </>
  );
}
