"use client";
// 튜닝 — 모델 선택 → 잡 생성 → 플랜 → 배치 (PRD E3/E6/E7)
import { useCallback, useEffect, useState } from "react";
import { api, fmt } from "@/lib/api";

type Job = { job_id: string; model_id: string; dataset_version: string; record_count: number;
             status: string; triggered_by: string; progress_pct: number;
             current_step: number; total_steps: number; error: string | null };
type Model = { model_id: string; status: string };

export default function TuningPage() {
  const [models, setModels] = useState<Model[]>([]);
  const [modelId, setModelId] = useState("");
  const [datasetVersion, setDatasetVersion] = useState("v0.1.0");
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

  // running 잡이 있으면 2초 주기 자동 새로고침 (실시간 진행률 모니터링)
  useEffect(() => {
    if (!jobs.some((j) => j.status === "running")) return;
    const t = setInterval(load, 2000);
    return () => clearInterval(t);
  }, [jobs, load]);

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
  const exportModel = (jobId: string) => {
    // tar.gz 다운로드 — 프록시 경유 브라우저 저장
    window.location.href = `/api/v1/tuning/jobs/${jobId}/export`;
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
          <button onClick={run(() => api("POST", "/api/v1/tuning/jobs", { model_id: modelId, dataset_version: datasetVersion }))}>잡 제출</button>
        </div>
        <p style={{ color: "var(--sub)", fontSize: 12.5, margin: "4px 0 0" }}>
          실학습은 GPU worker 가 플랜(YAML)으로 실행 — 여기서는 잡·플랜·상태 관리.
        </p>
      </section>
      <section className="panel">
        <h2>야간 배치 (E6)</h2>
        <div className="row">
          <button className="ghost" onClick={run(() => api("GET", "/api/v1/batch/should-run"))}>트리거 판정</button>
          <button onClick={run(() => api("POST", "/api/v1/batch/run", {}))}>배치 실행</button>
          <button className="ghost" onClick={run(() => api("GET", "/api/v1/batch/runs"))}>배치 이력</button>
        </div>
      </section>
      <section className="panel">
        <h2>잡 목록</h2>
        <table>
          <thead><tr><th>job_id</th><th>model</th><th>dataset</th><th>records</th><th>status</th><th>by</th><th>액션</th></tr></thead>
          <tbody>
            {jobs.map((j) => {
              const cls = j.status === "succeeded" ? " ok" : j.status === "failed" ? " bad" : "";
              return (
                <tr key={j.job_id}>
                  <td>{j.job_id}</td><td>{j.model_id}</td><td>{j.dataset_version}</td>
                  <td>{j.record_count}</td>
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
                    <button className="ghost btn-pill" onClick={run(async () =>
                      (await api<{ plan: string }>("GET", `/api/v1/tuning/jobs/${j.job_id}/plan`)).plan)}>플랜</button>{" "}
                    {j.status === "succeeded" && (
                      <button className="btn-pill" onClick={() => exportModel(j.job_id)}>다운로드</button>
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
