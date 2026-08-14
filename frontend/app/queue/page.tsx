"use client";
// 검수 큐 — 3단계 탐색: ①그룹(dataset_version) → ②세부 목록 → ③레코드 내용 (PRD §7.15 그룹핑 UX)
// 하단 로그 영역은 선택 그룹 요약을 표시. 시간은 locale 반영(PRD 시간 표기 원칙).
import { useCallback, useEffect, useState } from "react";
import { api, fmt, toLocale } from "@/lib/api";

type Group = { dataset_version: string; count: number; grades: Record<string, number>;
               task_types: Record<string, number>; sources: Record<string, number>;
               first_created_at: string | null; last_created_at: string | null };
type Item = { record_id: string; task_type: string; quality_grade: string;
              lineage_of: string | null; source_uri: string | null; license: string | null;
              created_at: string };
type Detail = { record_id: string; review_state: string; quality_grade: string;
                lineage_of: string | null; reviewer: string | null; created_at: string;
                payload: { messages: { role: string; content: string }[]; metadata: Record<string, unknown> } };

export default function QueuePage() {
  const [state, setState] = useState("pending");
  const [groups, setGroups] = useState<Group[]>([]);
  const [group, setGroup] = useState<Group | null>(null); // ② 선택된 그룹
  const [items, setItems] = useState<Item[]>([]);
  const [reviewer, setReviewer] = useState("supervisor");
  const [detail, setDetail] = useState<Detail | null>(null); // ③ 레코드 내용
  const [out, setOut] = useState("-");

  const loadGroups = useCallback(async () => {
    try {
      const data = await api<{ groups: Group[] }>("GET", `/api/v1/records/queue/groups?state=${state}`);
      setGroups(data.groups);
      return data.groups;
    } catch (e) { setOut(String(e)); return []; }
  }, [state]);

  const loadItems = useCallback(async (dv: string) => {
    try {
      const q = new URLSearchParams({ state, dataset_version: dv });
      const data = await api<{ items: Item[] }>("GET", `/api/v1/records/queue?${q}`);
      setItems(data.items);
    } catch (e) { setOut(String(e)); }
  }, [state]);

  useEffect(() => { setGroup(null); setDetail(null); loadGroups(); }, [loadGroups]);

  // 모달 ESC 닫기 (div 팝업 접근성)
  useEffect(() => {
    if (!detail) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setDetail(null); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [detail]);

  const openGroup = async (g: Group) => {
    setGroup(g);
    setDetail(null);
    setOut(fmt(g)); // 하단 로그 = 그룹 요약
    await loadItems(g.dataset_version);
  };

  const refresh = async () => {
    const gs = await loadGroups();
    if (group) {
      const cur = gs.find((g) => g.dataset_version === group.dataset_version) ?? null;
      setGroup(cur);
      if (cur) { setOut(fmt(cur)); await loadItems(cur.dataset_version); }
      else { setItems([]); setDetail(null); }
    }
  };

  const openDetail = async (rid: string) => {
    try { setDetail(await api<Detail>("GET", `/api/v1/records/${rid}`)); }
    catch (e) { setOut(String(e)); }
  };

  const review = async (rid: string, action: "approve" | "reject") => {
    try {
      await api("POST", `/api/v1/records/${rid}/review`, { action, reviewer });
      setDetail(null);
      await refresh();
    } catch (e) { setOut(String(e)); }
  };

  const reviewGroup = async (dv: string, action: "approve" | "reject") => {
    // 그룹 일괄 처리 확인 팝업 — 반려는 증강본 연쇄 폐기 포함 (PRD §7.15)
    const label = action === "approve" ? "전체 승인" : "전체 반려(증강본 연쇄 폐기 포함)";
    if (!window.confirm(`그룹 '${dv}' 의 pending 레코드를 ${label} 할까요?`)) return;
    try {
      setOut(fmt(await api("POST", "/api/v1/records/queue/review-group",
        { dataset_version: dv, action, reviewer })));
      setDetail(null);
      await refresh();
    } catch (e) { setOut(String(e)); }
  };

  const remove = async (rid: string) => {
    // 사용자 확인 팝업 — 증강본 연쇄 삭제 포함, 되돌릴 수 없음
    if (!window.confirm(`레코드 '${rid}' 를 삭제할까요?\n증강본(lineage)도 함께 삭제되며 되돌릴 수 없습니다.`)) return;
    try {
      await api("DELETE", `/api/v1/records/${rid}`);
      if (detail?.record_id === rid) setDetail(null);
      await refresh();
    } catch (e) { setOut(String(e)); }
  };

  return (
    <>
      <section className="panel">
        <h2>검수 큐 — ① 그룹 (dataset_version)</h2>
        <div className="row">
          <select value={state} onChange={(e) => setState(e.target.value)} aria-label="review state">
            {["pending", "approved", "rejected"].map((s) => <option key={s}>{s}</option>)}
          </select>
          <input type="text" value={reviewer} onChange={(e) => setReviewer(e.target.value)} aria-label="reviewer" />
          <button className="ghost" onClick={refresh}>새로고침</button>
          <span className="pill">그룹 클릭 = 세부 목록 · 세부 행 클릭 = 레코드 내용</span>
        </div>
        <table>
          <thead><tr><th>dataset_version</th><th>건수</th><th>grade 분포</th><th>task_type</th><th>출처 수</th><th>수집 시각(최근)</th><th>일괄 액션</th></tr></thead>
          <tbody>
            {groups.map((g) => (
              <tr key={g.dataset_version}
                  className={"selectable" + (group?.dataset_version === g.dataset_version ? " selected" : "")}
                  onClick={() => openGroup(g)}>
                <td>{g.dataset_version}</td>
                <td><span className="pill">{g.count}</span></td>
                <td>{Object.entries(g.grades).map(([k, v]) => `${k}:${v}`).join(" · ")}</td>
                <td>{Object.keys(g.task_types).join(", ")}</td>
                <td title={Object.entries(g.sources).map(([k, v]) => `${k} (${v})`).join("\n")}>
                  {Object.keys(g.sources).length}
                </td>
                <td>{toLocale(g.last_created_at ?? "")}</td>
                <td onClick={(e) => e.stopPropagation()}>
                  {state === "pending" && (
                    <>
                      <button className="ghost" onClick={() => reviewGroup(g.dataset_version, "approve")}>전체 승인</button>{" "}
                      <button className="ghost" style={{ color: "var(--bad)", borderColor: "var(--bad)" }}
                              onClick={() => reviewGroup(g.dataset_version, "reject")}>전체 반려</button>
                    </>
                  )}
                </td>
              </tr>
            ))}
            {groups.length === 0 && <tr><td colSpan={7} style={{ color: "var(--sub)" }}>해당 상태의 레코드 없음</td></tr>}
          </tbody>
        </table>
      </section>

      {group && (
        <section className="panel">
          <h2 style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
            <span>② 세부 목록 — {group.dataset_version}</span>
            <span className="pill">{items.length}건</span>
            {state === "pending" && (
              <>
                <button className="btn-pill" onClick={() => reviewGroup(group.dataset_version, "approve")}>전체 승인</button>
                <button className="ghost btn-pill" style={{ color: "var(--bad)", borderColor: "var(--bad)" }}
                        onClick={() => reviewGroup(group.dataset_version, "reject")}>전체 반려</button>
              </>
            )}
            <button className="ghost btn-pill" onClick={() => { setGroup(null); setDetail(null); }}>그룹 목록으로</button>
          </h2>
          <table>
            <thead><tr><th>record_id</th><th>task_type</th><th>grade</th><th>lineage</th><th>출처</th><th>created</th><th>액션</th></tr></thead>
            <tbody>
              {items.map((it) => (
                <tr key={it.record_id}
                    className={"selectable" + (detail?.record_id === it.record_id ? " selected" : "")}
                    onClick={() => openDetail(it.record_id)}>
                  <td>{it.record_id}</td><td>{it.task_type}</td>
                  <td><span className={"pill" + (it.quality_grade === "gold" ? " ok" : "")}>{it.quality_grade}</span></td>
                  <td>{it.lineage_of ?? "-"}</td>
                  {/* F14 출처 상시 표시 — URI 축약 + license 툴팁 */}
                  <td title={`${it.source_uri ?? "-"} · license: ${it.license ?? "-"}`}
                      style={{ maxWidth: 180, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {it.source_uri ?? "-"}
                  </td>
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
      )}

      {detail && (
        // ③ 레코드 내용 — div 팝업(모달): 세부 목록을 이동하며 연속 검수 (PRD §7.15, 하단 스크롤 제거)
        <div role="dialog" aria-modal="true" aria-label={`레코드 내용 ${detail.record_id}`}
             onClick={() => setDetail(null)}
             style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.45)", zIndex: 1000,
                      display: "flex", alignItems: "center", justifyContent: "center", padding: 24 }}>
        <section className="panel" onClick={(e) => e.stopPropagation()}
                 style={{ margin: 0, width: "min(980px, 100%)", maxHeight: "85vh", overflowY: "auto" }}>
          <h2 style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
            <span>③ 레코드 내용 — {detail.record_id}</span>
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
            <span className="pill">출처: {String(detail.payload.metadata.source_uri ?? "-")}</span>
            <span className="pill">license: {String(detail.payload.metadata.license ?? "-")}</span>
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
        </div>
      )}
      {/* 하단 로그 = 선택 그룹 요약 (그룹 미선택 시 최근 동작/오류) */}
      <pre className="out">{out}</pre>
    </>
  );
}
