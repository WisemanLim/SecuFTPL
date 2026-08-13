"use client";
// 모델 선택 — 레지스트리 시드·다운로드·pin·상세 (PRD F2/E7)
import { useCallback, useEffect, useState } from "react";
import { api, fmt } from "@/lib/api";

type Model = { model_id: string; tier: string; role: string; family: string;
               param_size_b: number | null; status: string; revision: string | null };
type Detail = {
  model_id: string; tier: string; role: string; family: string; param_size_b: number | null;
  license: string | null; status: string; revision: string | null; notes: string;
  download_plan: string; snapshot_manifest: Record<string, unknown> | null;
  usable_for_training: boolean;
};

const STATUS_CLS: Record<string, string> = {
  downloaded: " ok", pinned: " ok", downloading: "", registered: "", candidate: "", retired: " bad",
};

export default function ModelsPage() {
  const [models, setModels] = useState<Model[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [detail, setDetail] = useState<Detail | null>(null);
  const [profile, setProfile] = useState("pilot");
  const [revision, setRevision] = useState("");
  const [out, setOut] = useState("-");

  const load = useCallback(async () => {
    try { setModels((await api<{ models: Model[] }>("GET", "/api/v1/models")).models); }
    catch (e) { setOut(String(e)); }
  }, []);
  useEffect(() => { load(); }, [load]);

  // downloading 진행 중이면 2초 폴링
  useEffect(() => {
    if (!models.some((m) => m.status === "downloading")) return;
    const t = setInterval(load, 2000);
    return () => clearInterval(t);
  }, [models, load]);

  const openDetail = async (modelId: string) => {
    setSelected(modelId);
    try { setDetail(await api<Detail>("GET", `/api/v1/models/${modelId}/detail`)); }
    catch (e) { setOut(String(e)); }
  };
  const refreshAll = async () => {
    await load();
    if (selected) { try { setDetail(await api<Detail>("GET", `/api/v1/models/${selected}/detail`)); } catch { /* keep */ } }
  };
  const act = (fn: () => Promise<unknown>) => async () => {
    try { setOut(fmt(await fn())); await refreshAll(); } catch (e) { setOut(String(e)); }
  };

  return (
    <>
      <section className="panel">
        <h2>모델 레지스트리 <span className="pill">행 클릭 = 상세</span></h2>
        <div className="row">
          <select value={profile} onChange={(e) => setProfile(e.target.value)} aria-label="시드 프로파일">
            <option value="pilot">pilot (12)</option><option value="core">core</option><option value="all">all</option>
          </select>
          <button className="ghost" onClick={act(() => api("POST", "/api/v1/models/seed", { profile }))}>카탈로그 시드</button>
          <span className="pill">{selected ?? "선택 없음"}</span>
        </div>
        <table>
          <thead><tr><th>model_id</th><th>tier</th><th>role</th><th>family</th><th>size(B)</th><th>status</th><th>revision</th></tr></thead>
          <tbody>
            {models.map((m) => (
              <tr key={m.model_id} className={"selectable" + (selected === m.model_id ? " selected" : "")}
                  onClick={() => openDetail(m.model_id)}>
                <td>{m.model_id}</td><td>{m.tier}</td><td>{m.role}</td><td>{m.family}</td>
                <td>{m.param_size_b ?? "-"}</td>
                <td><span className={"pill" + (STATUS_CLS[m.status] ?? "")}>{m.status}</span></td>
                <td>{m.revision ?? "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {detail && (
        <section className="panel">
          <h2 style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
            <span>모델 상세 — {detail.model_id}</span>
            <span className={"pill" + (STATUS_CLS[detail.status] ?? "")}>{detail.status}</span>
            {detail.usable_for_training
              ? <span className="pill ok">학습 사용 가능</span>
              : <span className="pill">다운로드 필요</span>}
            {(detail.status === "registered" || detail.status === "candidate") && (
              <button className="btn-pill" onClick={act(() => api("POST", `/api/v1/models/${detail.model_id}/download`))}>다운로드</button>
            )}
            {detail.status === "downloading" && <span className="pill">다운로드 중...</span>}
            <input type="text" placeholder="revision" value={revision} onChange={(e) => setRevision(e.target.value)}
                   style={{ minWidth: 140 }} aria-label="pin revision" />
            <button className="ghost btn-pill" onClick={act(() => api("POST", `/api/v1/models/${detail.model_id}/pin`, { revision }))}>pin</button>
            <button className="ghost btn-pill" onClick={() => setDetail(null)}>닫기</button>
          </h2>
          <table>
            <tbody>
              <tr><th style={{ width: 130 }}>tier / role</th><td>{detail.tier} / {detail.role}</td></tr>
              <tr><th>family / size</th><td>{detail.family} / {detail.param_size_b ?? "-"}B</td></tr>
              <tr><th>license</th><td>{detail.license ?? "미확인 (모델카드 확인 필요)"}</td></tr>
              <tr><th>revision</th><td>{detail.revision ?? "-"}</td></tr>
              <tr><th>notes</th><td>{detail.notes || "-"}</td></tr>
            </tbody>
          </table>
          <h3 style={{ fontSize: 13.5, margin: "10px 0 2px" }}>다운로드 플랜 (hf CLI)</h3>
          <pre className="out" style={{ maxHeight: 120 }}>{detail.download_plan}</pre>
          {detail.snapshot_manifest && (
            <>
              <h3 style={{ fontSize: 13.5, margin: "10px 0 2px" }}>스냅샷 매니페스트 (다운로드 완료)</h3>
              <pre className="out" style={{ maxHeight: 160 }}>{fmt(detail.snapshot_manifest)}</pre>
            </>
          )}
        </section>
      )}
      <pre className="out">{out}</pre>
    </>
  );
}
