"use client";
// 리더보드 — 모델 간 평가 비교 + 모델 선택 시 세부내용 (PRD F1/E3/E7)
import { useCallback, useEffect, useState } from "react";
import { api, toLocale } from "@/lib/api";

type Row = { model_id: string; dataset_version: string; baseline: boolean; cases: number;
             json_valid_rate: number; severity_accuracy: number; exact_match_rate: number;
             attack_f1: number };
type Detail = {
  model_id: string;
  evaluations: (Row & { eval_id: number; job_id: string | null; attack_precision: number;
                        attack_recall: number; at: string })[];
  jobs: { job_id: string; dataset_version: string; status: string; record_count: number;
          adapter_uri: string | null; triggered_by: string; at: string }[];
};

type EvalGuide = { task_type: string; recommended_metrics: string[]; guide: Record<string, string>;
                   case_count: number | null; reliability_note: string | null };
const TASK_TYPES = ["alert_triage", "cti_extraction", "vuln_triage", "policy_qa", "safety_refusal"];

export default function LeaderboardPage() {
  const [items, setItems] = useState<Row[]>([]);
  const [sortBy, setSortBy] = useState("attack_f1");
  const [detail, setDetail] = useState<Detail | null>(null);
  const [error, setError] = useState("");

  // F12: 평가지표 가이드·추천
  const [guideTaskType, setGuideTaskType] = useState("alert_triage");
  const [guideCaseCount, setGuideCaseCount] = useState<number | "">("");
  const [guide, setGuide] = useState<EvalGuide | null>(null);
  const loadGuide = async () => {
    try {
      const q = guideCaseCount === "" ? "" : `&case_count=${guideCaseCount}`;
      setGuide(await api<EvalGuide>("GET", `/api/v1/tuning/eval-guide?task_type=${guideTaskType}${q}`));
    } catch (e) { setError(String(e)); }
  };

  const load = useCallback(async () => {
    try {
      const data = await api<{ items: Row[] }>("GET", `/api/v1/tuning/leaderboard?sort_by=${sortBy}`);
      setItems(data.items);
      setError("");
    } catch (e) { setError(String(e)); }
  }, [sortBy]);
  useEffect(() => { load(); }, [load]);

  const [modelId, setModelId] = useState<string | null>(null);
  const openDetail = async (mid: string) => {
    try {
      setModelId(mid);
      setDetail(await api<Detail>("GET", `/api/v1/tuning/leaderboard/detail/${mid}`));
      setError("");
    } catch (e) { setError(String(e)); }
  };
  const refreshAll = async (mid: string | null) => {
    await load();
    if (mid) { try { setDetail(await api<Detail>("GET", `/api/v1/tuning/leaderboard/detail/${mid}`)); } catch { setDetail(null); } }
  };
  const delEval = async (evalId: number) => {
    if (!window.confirm(`평가 결과 #${evalId} 삭제? (되돌릴 수 없음)`)) return;
    try { await api("DELETE", `/api/v1/tuning/leaderboard/${evalId}`); await refreshAll(modelId); }
    catch (e) { setError(String(e)); }
  };
  const retryJob = async (jobId: string) => {
    try { await api("POST", `/api/v1/tuning/jobs/${jobId}/retry`); await refreshAll(modelId); }
    catch (e) { setError(String(e)); }
  };
  const delJob = async (jobId: string) => {
    if (!window.confirm(`잡 '${jobId}' 삭제? (이벤트 로그 포함)`)) return;
    try { await api("DELETE", `/api/v1/tuning/jobs/${jobId}`); await refreshAll(modelId); }
    catch (e) { setError(String(e)); }
  };

  return (
    <>
      <section className="panel">
        <h2>평가지표 가이드·추천 <span className="pill">F12</span></h2>
        <div className="row">
          <select value={guideTaskType} onChange={(e) => setGuideTaskType(e.target.value)} aria-label="guide task type">
            {TASK_TYPES.map((t) => <option key={t}>{t}</option>)}
          </select>
          <input type="number" min={0} placeholder="표본 건수(선택)" style={{ width: 130 }}
                 value={guideCaseCount}
                 onChange={(e) => setGuideCaseCount(e.target.value === "" ? "" : Number(e.target.value))}
                 aria-label="case count" />
          <button className="ghost" onClick={loadGuide}>추천 지표 조회</button>
        </div>
        {guide && (
          <div style={{ marginTop: 8 }}>
            <p style={{ margin: "0 0 4px" }}>
              <b>{guide.task_type}</b> 추천 지표: {guide.recommended_metrics.map((m) => <span key={m} className="pill" style={{ marginRight: 4 }}>{m}</span>)}
            </p>
            <ul style={{ margin: "4px 0", paddingLeft: 18, fontSize: 12.5, color: "var(--sub)" }}>
              {Object.entries(guide.guide).map(([m, text]) => <li key={m}><b>{m}</b>: {text}</li>)}
            </ul>
            {guide.reliability_note && (
              <p style={{ fontSize: 12.5, color: "var(--sub)" }}>표본 신뢰도: {guide.reliability_note}</p>
            )}
          </div>
        )}
      </section>
      <section className="panel">
        <h2>모델 평가 리더보드 <span className="pill">행 클릭 = 세부내용</span></h2>
        <div className="row">
          <select value={sortBy} onChange={(e) => setSortBy(e.target.value)} aria-label="sort by">
            {["attack_f1", "json_valid_rate", "severity_accuracy", "exact_match_rate"].map((s) => <option key={s}>{s}</option>)}
          </select>
          <button className="ghost" onClick={load}>새로고침</button>
        </div>
        {error && <pre className="out">{error}</pre>}
        <table>
          <thead><tr><th>#</th><th>model</th><th>dataset</th><th>baseline</th><th>cases</th>
            <th>json_valid</th><th>severity</th><th>exact</th><th>attack_f1</th></tr></thead>
          <tbody>
            {items.map((r, i) => (
              <tr key={`${r.model_id}-${r.dataset_version}-${i}`}
                  className={"selectable" + (detail?.model_id === r.model_id ? " selected" : "")}
                  onClick={() => openDetail(r.model_id)}>
                <td>{i + 1}</td><td>{r.model_id}</td><td>{r.dataset_version}</td>
                <td>{r.baseline ? <span className="pill">baseline</span> : ""}</td>
                <td>{r.cases}</td><td>{r.json_valid_rate.toFixed(3)}</td>
                <td>{r.severity_accuracy.toFixed(3)}</td><td>{r.exact_match_rate.toFixed(3)}</td>
                <td><b>{r.attack_f1.toFixed(3)}</b></td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {detail && (
        <section className="panel">
          <h2 style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
            <span>모델 세부내용 — {detail.model_id}</span>
            <button className="ghost btn-pill" onClick={() => setDetail(null)}>닫기</button>
          </h2>
          <h3 style={{ fontSize: 13.5, margin: "10px 0 2px" }}>평가 이력 ({detail.evaluations.length})</h3>
          <table>
            <thead><tr><th>at</th><th>dataset</th><th>job</th><th>cases</th>
              <th>json_valid</th><th>severity</th><th>exact</th>
              <th>precision</th><th>recall</th><th>attack_f1</th><th>액션</th></tr></thead>
            <tbody>
              {detail.evaluations.map((e) => (
                <tr key={`e-${e.eval_id}`}>
                  <td>{toLocale(e.at)}</td><td>{e.dataset_version}</td>
                  <td>{e.job_id ?? <span className="pill">baseline</span>}</td>
                  <td>{e.cases}</td><td>{e.json_valid_rate.toFixed(3)}</td>
                  <td>{e.severity_accuracy.toFixed(3)}</td><td>{e.exact_match_rate.toFixed(3)}</td>
                  <td>{e.attack_precision.toFixed(3)}</td><td>{e.attack_recall.toFixed(3)}</td>
                  <td><b>{e.attack_f1.toFixed(3)}</b></td>
                  <td><button className="ghost btn-pill" style={{ color: "var(--bad)", borderColor: "var(--bad)" }}
                          onClick={() => delEval(e.eval_id)}>삭제</button></td>
                </tr>
              ))}
            </tbody>
          </table>
          <h3 style={{ fontSize: 13.5, margin: "12px 0 2px" }}>튜닝 잡 ({detail.jobs.length})</h3>
          <table>
            <thead><tr><th>at</th><th>job_id</th><th>dataset</th><th>records</th>
              <th>status</th><th>adapter</th><th>by</th><th>액션</th></tr></thead>
            <tbody>
              {detail.jobs.map((j) => {
                const cls = j.status === "succeeded" ? " ok" : j.status === "failed" ? " bad" : "";
                return (
                  <tr key={j.job_id}>
                    <td>{toLocale(j.at)}</td><td>{j.job_id}</td><td>{j.dataset_version}</td>
                    <td>{j.record_count}</td>
                    <td><span className={"pill" + cls}>{j.status}</span></td>
                    <td>{j.adapter_uri ?? "-"}</td><td>{j.triggered_by}</td>
                    <td>
                      {(j.status === "queued" || j.status === "failed") && (
                        <button className="btn-pill" onClick={() => retryJob(j.job_id)}>재실행</button>
                      )}{" "}
                      {j.status !== "running" && (
                        <button className="ghost btn-pill" style={{ color: "var(--bad)", borderColor: "var(--bad)" }}
                                onClick={() => delJob(j.job_id)}>삭제</button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </section>
      )}
    </>
  );
}
