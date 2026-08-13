"use client";
// 검수 큐 — 승인/반려 + 레코드 내용 확인, 시간은 locale 반영 (PRD §7.3 ⑨·시간 표기 원칙)
import { useCallback, useEffect, useState } from "react";
import { api, fmt, toLocale } from "@/lib/api";

type Item = { record_id: string; task_type: string; quality_grade: string;
              lineage_of: string | null; created_at: string };
type Detail = { record_id: string; review_state: string; quality_grade: string;
                lineage_of: string | null; reviewer: string | null; created_at: string;
                payload: { messages: { role: string; content: string }[]; metadata: Record<string, unknown> } };

export default function QueuePage() {
  const [state, setState] = useState("pending");
  const [items, setItems] = useState<Item[]>([]);
  const [reviewer, setReviewer] = useState("supervisor");
  const [detail, setDetail] = useState<Detail | null>(null);
  const [out, setOut] = useState("-");

  const load = useCallback(async () => {
    try {
      const data = await api<{ items: Item[] }>("GET", `/api/v1/records/queue?state=${state}`);
      setItems(data.items);
    } catch (e) { setOut(String(e)); }
  }, [state]);
  useEffect(() => { load(); }, [load]);

  const openDetail = async (rid: string) => {
    try { setDetail(await api<Detail>("GET", `/api/v1/records/${rid}`)); }
    catch (e) { setOut(String(e)); }
  };

  const review = async (rid: string, action: "approve" | "reject") => {
    try {
      setOut(fmt(await api("POST", `/api/v1/records/${rid}/review`, { action, reviewer })));
      setDetail(null);
      await load();
    } catch (e) { setOut(String(e)); }
  };

  const remove = async (rid: string) => {
    // 사용자 확인 팝업 — 증강본 연쇄 삭제 포함, 되돌릴 수 없음
    if (!window.confirm(`레코드 '${rid}' 를 삭제할까요?\n증강본(lineage)도 함께 삭제되며 되돌릴 수 없습니다.`)) return;
    try {
      setOut(fmt(await api("DELETE", `/api/v1/records/${rid}`)));
      if (detail?.record_id === rid) setDetail(null);
      await load();
    } catch (e) { setOut(String(e)); }
  };

  return (
    <>
      <section className="panel">
        <h2>검수 큐</h2>
        <div className="row">
          <select value={state} onChange={(e) => setState(e.target.value)} aria-label="review state">
            {["pending", "approved", "rejected"].map((s) => <option key={s}>{s}</option>)}
          </select>
          <input type="text" value={reviewer} onChange={(e) => setReviewer(e.target.value)} aria-label="reviewer" />
          <button className="ghost" onClick={load}>새로고침</button>
          <span className="pill">행 클릭 = 내용 확인</span>
        </div>
        <table>
          <thead><tr><th>record_id</th><th>task_type</th><th>grade</th><th>lineage</th><th>created</th><th>액션</th></tr></thead>
          <tbody>
            {items.map((it) => (
              <tr key={it.record_id}
                  className={"selectable" + (detail?.record_id === it.record_id ? " selected" : "")}
                  onClick={() => openDetail(it.record_id)}>
                <td>{it.record_id}</td><td>{it.task_type}</td>
                <td><span className={"pill" + (it.quality_grade === "gold" ? " ok" : "")}>{it.quality_grade}</span></td>
                <td>{it.lineage_of ?? "-"}</td>
                <td>{toLocale(it.created_at)}</td>
                <td onClick={(e) => e.stopPropagation()}>
                  {state === "pending" && (
                    <>
                      <button className="ghost" onClick={() => review(it.record_id, "approve")}>승인</button>{" "}
                      <button className="ghost" onClick={() => review(it.record_id, "reject")}>반려</button>{" "}
                    </>
                  )}
                  <button className="ghost" style={{ color: "var(--bad)", borderColor: "var(--bad)" }}
                          onClick={() => remove(it.record_id)}>삭제</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {detail && (
        <section className="panel">
          <h2 style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
            <span>레코드 내용 — {detail.record_id}</span>
            <span className={"pill" + (detail.review_state === "approved" ? " ok"
                : detail.review_state === "rejected" ? " bad" : "")}>{detail.review_state}</span>
            {/* 상태 pill 바로 옆 — pill 과 동일 글자/형태(btn-pill), 색상은 기존 유지 */}
            {detail.review_state === "pending" && (
              <>
                <button className="btn-pill" onClick={() => review(detail.record_id, "approve")}>승인</button>
                <button className="ghost btn-pill" onClick={() => review(detail.record_id, "reject")}>반려</button>
              </>
            )}
            <button className="ghost btn-pill" style={{ color: "var(--bad)", borderColor: "var(--bad)" }}
                    onClick={() => remove(detail.record_id)}>삭제</button>
            <button className="ghost btn-pill" onClick={() => setDetail(null)}>닫기</button>
          </h2>
          <div className="row" style={{ fontSize: 12.5, color: "var(--sub)" }}>
            <span className="pill">grade: {detail.quality_grade}</span>
            {detail.lineage_of && <span className="pill">lineage: {detail.lineage_of}</span>}
            {detail.reviewer && <span className="pill">reviewer: {detail.reviewer}</span>}
            <span className="pill">created: {toLocale(detail.created_at)}</span>
          </div>
          <table>
            <thead><tr><th style={{ width: 90 }}>role</th><th>content</th></tr></thead>
            <tbody>
              {detail.payload.messages.map((m, i) => (
                <tr key={`${m.role}-${i}`}>
                  <td><span className="pill">{m.role}</span></td>
                  <td style={{ whiteSpace: "pre-wrap", fontFamily: "ui-monospace, Menlo, monospace", fontSize: 12 }}>
                    {m.content}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <pre className="out">{fmt(detail.payload.metadata)}</pre>
        </section>
      )}
      <pre className="out">{out}</pre>
    </>
  );
}
