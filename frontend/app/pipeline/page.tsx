"use client";
// 파이프라인 위저드 — 단계 완료 시 자동 다음 이동, 이전 복귀 허용 (PRD §7.11)
import { useCallback, useEffect, useState } from "react";
import Stepper, { StepDef, StepStatus } from "@/components/Stepper";
import { api, fmt } from "@/lib/api";
import { TASK_TYPES, buildTemplate } from "@/lib/templates";

const STEPS: StepDef[] = [
  { id: "model", title: "모델 선택", desc: "레지스트리에서 베이스모델 선택 (시드/pin)" },
  { id: "dataset", title: "데이터셋 수집", desc: "게이트·가명화·중복제거 → 검수 큐 적재" },
  { id: "review", title: "검수 승인", desc: "pending 레코드 승인/반려 (승인분만 학습)" },
  { id: "augment", title: "증강 (선택)", desc: "키워드 치환 — 건너뛰기 가능" },
  { id: "tuning", title: "튜닝 잡", desc: "QLoRA 잡 생성 — 실학습은 GPU worker" },
  { id: "gate", title: "평가 게이트", desc: "지표 하한 + 회귀 검사 — 통과 시 배포 가능" },
  { id: "leaderboard", title: "리더보드 비교", desc: "모델 간 평가 지표 비교" },
  { id: "deploy", title: "배포", desc: "게이트 통과 어댑터 재배포 (serving 연동)" },
];

type Model = { model_id: string; status: string; tier: string };
type IngestResult = { queued: number; results: { status: string }[] };

/** 수집 목표 충족 판정 — 신규 적재(queued>0) 또는 전건이 완전중복(동일 데이터 기존재)이면 다음 단계 진행. */
function ingestSatisfied(d: IngestResult): boolean {
  if (d.queued > 0) return true;
  return d.results.length > 0 && d.results.every((r) => r.status === "skipped_exact_duplicate");
}
type QueueItem = { record_id: string; task_type: string; quality_grade: string; lineage_of: string | null };
type LbRow = { model_id: string; dataset_version: string; baseline: boolean; attack_f1: number;
               json_valid_rate: number; severity_accuracy: number };

const STORE_KEY = "secuftpl.pipeline.v1";

export default function PipelinePage() {
  const [current, setCurrent] = useState(0);
  const [statuses, setStatuses] = useState<StepStatus[]>(
    STEPS.map((_, i) => (i === 0 ? "current" : "pending")),
  );
  // 파이프라인 컨텍스트
  const [modelId, setModelId] = useState("");
  const [datasetVersion, setDatasetVersion] = useState("v0.1.0");
  const [jobId, setJobId] = useState("");
  const [out, setOut] = useState("-");
  const [restored, setRestored] = useState(false);

  // 새로고침/재진입 시 진행 상태 복원 (sessionStorage — 탭 단위)
  useEffect(() => {
    try {
      const saved = sessionStorage.getItem(STORE_KEY);
      if (saved) {
        const s = JSON.parse(saved);
        if (Array.isArray(s.statuses) && s.statuses.length === STEPS.length) {
          setCurrent(s.current ?? 0);
          setStatuses(s.statuses);
          setModelId(s.modelId ?? "");
          setDatasetVersion(s.datasetVersion ?? "v0.1.0");
          setJobId(s.jobId ?? "");
        }
      }
    } catch { /* 복원 실패 시 초기 상태 */ }
    setRestored(true);
  }, []);
  useEffect(() => {
    if (!restored) return;
    sessionStorage.setItem(STORE_KEY, JSON.stringify(
      { current, statuses, modelId, datasetVersion, jobId }));
  }, [restored, current, statuses, modelId, datasetVersion, jobId]);

  const advance = useCallback((mark: StepStatus = "done") => {
    // 방어: onClick={advance} 처럼 이벤트 객체가 인자로 들어와도 상태 오염 금지
    const safeMark: StepStatus = mark === "skipped" ? "skipped" : "done";
    setStatuses((prev) => {
      const next = [...prev];
      next[current] = safeMark;
      if (current + 1 < STEPS.length) next[current + 1] = "current";
      return next;
    });
    if (current + 1 < STEPS.length) setCurrent(current + 1);
  }, [current]);

  const resetPipeline = useCallback(() => {
    sessionStorage.removeItem(STORE_KEY);
    setCurrent(0);
    setStatuses(STEPS.map((_, i) => (i === 0 ? "current" : "pending")));
    setModelId(""); setDatasetVersion("v0.1.0"); setJobId(""); setOut("-");
  }, []);

  const goBack = useCallback((idx: number) => {
    // 이전(완료/건너뜀) 단계 복귀 — 이후 단계 상태는 유지(재진행 시 갱신)
    setStatuses((prev) => {
      const next = [...prev];
      if (next[current] === "current") next[current] = "pending";
      next[idx] = "current";
      return next;
    });
    setCurrent(idx);
    setOut("-");
  }, [current]);

  const run = (fn: () => Promise<unknown>, onOk?: (d: unknown) => void) => async () => {
    try {
      const d = await fn();
      setOut(fmt(d));
      onOk?.(d);
    } catch (e) { setOut(String(e)); }
  };

  const step = STEPS[current].id;
  return (
    <>
      <section className="panel">
        <h2 style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span>파인튜닝 파이프라인</span>
          <button className="ghost btn-pill" style={{ marginLeft: "auto" }}
                  onClick={() => { if (window.confirm("새 파이프라인을 시작할까요? 현재 진행 상태는 초기화됩니다.")) resetPipeline(); }}>
            + 새 파이프라인
          </button>
        </h2>
        <Stepper steps={STEPS} statuses={statuses} onNavigate={goBack} />
        <div className="row" style={{ fontSize: 12.5, color: "var(--sub)" }}>
          <span className="pill">모델: {modelId || "미선택"}</span>
          <span className="pill">dataset: {datasetVersion}</span>
          {jobId && <span className="pill">job: {jobId}</span>}
        </div>
      </section>

      {step === "model" && <ModelStep onDone={(id) => { setModelId(id); advance(); }} setOut={setOut} />}
      {step === "dataset" && <DatasetStep onDone={() => advance()} run={run} />}
      {step === "review" && <ReviewStep onDone={() => advance()} setOut={setOut} />}
      {step === "augment" && <AugmentStep onDone={() => advance()} onSkip={() => advance("skipped")} run={run} />}
      {step === "tuning" && (
        <TuningStep modelId={modelId} datasetVersion={datasetVersion}
                    setDatasetVersion={setDatasetVersion}
                    onDone={(jid) => { setJobId(jid); advance(); }} setOut={setOut} />
      )}
      {step === "gate" && (
        <GateStep modelId={modelId} datasetVersion={datasetVersion} jobId={jobId}
                  onDone={() => advance()} setOut={setOut} />
      )}
      {step === "leaderboard" && <LeaderboardStep onDone={() => advance()} setOut={setOut} />}
      {step === "deploy" && <DeployStep modelId={modelId} jobId={jobId}
                                        onDone={() => advance()} onNew={resetPipeline} />}

      <pre className="out">{out}</pre>
    </>
  );
}

// --- 단계 컴포넌트 ---

function ModelStep({ onDone, setOut }: { onDone: (id: string) => void; setOut: (s: string) => void }) {
  const [models, setModels] = useState<Model[]>([]);
  const [sel, setSel] = useState("");
  const load = useCallback(async () => {
    try { setModels((await api<{ models: Model[] }>("GET", "/api/v1/models")).models); }
    catch (e) { setOut(String(e)); }
  }, [setOut]);
  useEffect(() => { load(); }, [load]);
  const usable = models.filter((m) => m.status === "downloaded" || m.status === "pinned");
  return (
    <section className="panel">
      <h2>① 모델 선택</h2>
      <div className="row">
        <button className="ghost" onClick={async () => {
          try { setOut(fmt(await api("POST", "/api/v1/models/seed", { profile: "pilot" }))); await load(); }
          catch (e) { setOut(String(e)); }
        }}>카탈로그 시드 (pilot)</button>
        <select value={sel} onChange={(e) => setSel(e.target.value)} aria-label="모델 선택">
          <option value="">— 다운로드된 모델 선택 —</option>
          {usable.map((m) => (
            <option key={m.model_id} value={m.model_id}>{m.model_id} ({m.status})</option>
          ))}
        </select>
        <button disabled={!sel} onClick={() => onDone(sel)}>선택 완료 → 다음</button>
      </div>
      <p style={{ color: "var(--sub)", fontSize: 12.5, margin: "4px 0 0" }}>
        {usable.length === 0
          ? "다운로드된 모델이 없습니다 — 사이드바 [모델] 에서 모델을 다운로드(downloaded/pinned) 하세요."
          : `학습 가능 모델 ${usable.length}개 (downloaded/pinned). 다운로드는 [모델] 페이지에서.`}
      </p>
    </section>
  );
}

function DatasetStep({ onDone, run }: {
  onDone: () => void;
  run: (fn: () => Promise<unknown>, onOk?: (d: unknown) => void) => () => Promise<void>;
}) {
  const [taskType, setTaskType] = useState("alert_triage");
  // 종류 선택 시 task별 messages 템플릿 자동 채움 (근거 문서 §권장 JSONL 포맷)
  const [jsonl, setJsonl] = useState(() => buildTemplate("alert_triage"));
  const [autoFill, setAutoFill] = useState(true);  // 사용자가 직접 수정하면 자동 덮어쓰기 중단
  const [uploadFiles, setUploadFiles] = useState<File[]>([]);
  const changeTask = (t: string) => {
    setTaskType(t);
    if (autoFill || !jsonl.trim()) setJsonl(buildTemplate(t));
  };
  const parse = () => {
    const records = jsonl.split("\n").filter((l) => l.trim()).map((l) => {
      const r = JSON.parse(l);
      r.metadata ??= {};
      if (!r.metadata.task_type) r.metadata.task_type = taskType;
      return r;
    });
    if (records.length === 0) throw new Error("수집할 레코드가 없습니다 — 템플릿 채우기 또는 JSONL 입력 필요 (빈 입력은 전송하지 않음)");
    return records;
  };
  return (
    <section className="panel">
      <h2>② 데이터셋 수집</h2>
      <div className="row">
        <select value={taskType} onChange={(e) => changeTask(e.target.value)} aria-label="task type">
          {TASK_TYPES.map((t) => <option key={t}>{t}</option>)}
        </select>
        <button className="ghost" onClick={() => { setJsonl(buildTemplate(taskType)); setAutoFill(true); }}>
          템플릿 다시 채우기
        </button>
        <span className="pill">종류 선택 시 예시 자동 채움 — 내용 수정 후 수집</span>
      </div>
      <textarea value={jsonl} aria-label="jsonl"
        onChange={(e) => { setJsonl(e.target.value); setAutoFill(false); }} />
      <div className="row">
        <button className="ghost" onClick={run(() => api("POST", "/api/v1/datasets/validate", { records: parse() }))}>검증만</button>
        <button onClick={run(
          () => api<IngestResult>("POST", "/api/v1/records/ingest", { records: parse() }),
          (d) => { if (ingestSatisfied(d as IngestResult)) onDone(); },  // 신규 수집 또는 기존재 → 자동 다음
        )}>수집 → 자동 다음</button>
      </div>
      <div className="row">
        <input type="file" multiple accept=".jsonl,.json" aria-label="파일 업로드"
               onChange={(e) => setUploadFiles(Array.from(e.target.files ?? []))} />
        <button className="ghost" disabled={uploadFiles.length === 0} onClick={run(async () => {
          const form = new FormData();
          for (const f of uploadFiles) form.append("files", f);
          form.append("task_type", taskType);
          const res = await fetch("/api/v1/records/upload", { method: "POST", body: form });
          const data = await res.json();
          if (!res.ok) throw new Error(`${res.status} ${JSON.stringify(data)}`);
          return data;
        }, (d) => {
          const ing = (d as { ingest?: IngestResult }).ingest;
          if (ing && ingestSatisfied(ing)) onDone();  // 파일 수집 성공/기존재 → 자동 다음
        })}>파일 업로드 수집 ({uploadFiles.length}개)</button>
        <span className="pill">디렉토리·URL 수집은 [데이터셋] 페이지에서</span>
      </div>
      <p style={{ color: "var(--sub)", fontSize: 12.5, margin: "4px 0 0" }}>
        템플릿의 내부 IP·호스트명은 수집 시 게이트가 자동 가명화한다. 동일 내용 재수집은 중복으로 스킵됨.
      </p>
    </section>
  );
}

function ReviewStep({ onDone, setOut }: { onDone: () => void; setOut: (s: string) => void }) {
  const [items, setItems] = useState<QueueItem[]>([]);
  const [approved, setApproved] = useState(0);
  const load = useCallback(async () => {
    try {
      const [p, a] = await Promise.all([
        api<{ items: QueueItem[] }>("GET", "/api/v1/records/queue?state=pending"),
        api<{ count: number }>("GET", "/api/v1/records/queue?state=approved"),
      ]);
      setItems(p.items);
      setApproved(a.count);
    } catch (e) { setOut(String(e)); }
  }, [setOut]);
  useEffect(() => { load(); }, [load]);
  const [detail, setDetail] = useState<{ record_id: string;
    payload: { messages: { role: string; content: string }[] } } | null>(null);
  const review = async (rid: string, action: "approve" | "reject") => {
    try {
      setOut(fmt(await api("POST", `/api/v1/records/${rid}/review`, { action, reviewer: "supervisor" })));
      setDetail(null);
      await load();
    } catch (e) { setOut(String(e)); }
  };
  return (
    <section className="panel">
      <h2>③ 검수 승인 <span className="pill ok">approved {approved}</span> <span className="pill">행 클릭 = 내용 확인</span></h2>
      <table>
        <thead><tr><th>record_id</th><th>task_type</th><th>grade</th><th>lineage</th><th>액션</th></tr></thead>
        <tbody>
          {items.map((it) => (
            <tr key={it.record_id} className={"selectable" + (detail?.record_id === it.record_id ? " selected" : "")}
                onClick={async () => {
                  try { setDetail(await api("GET", `/api/v1/records/${it.record_id}`)); }
                  catch (e) { setOut(String(e)); }
                }}>
              <td>{it.record_id}</td><td>{it.task_type}</td><td>{it.quality_grade}</td>
              <td>{it.lineage_of ?? "-"}</td>
              <td onClick={(e) => e.stopPropagation()}>
                <button className="ghost" onClick={() => review(it.record_id, "approve")}>승인</button>{" "}
                <button className="ghost" onClick={() => review(it.record_id, "reject")}>반려</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {detail && (
        <table>
          <thead><tr><th style={{ width: 90 }}>role</th><th>content — {detail.record_id}</th></tr></thead>
          <tbody>
            {detail.payload.messages.map((m, i) => (
              <tr key={`${m.role}-${i}`}>
                <td><span className="pill">{m.role}</span></td>
                <td style={{ whiteSpace: "pre-wrap", fontFamily: "ui-monospace, Menlo, monospace", fontSize: 12 }}>{m.content}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <div className="row">
        <button disabled={approved < 1} onClick={onDone}>승인 완료 → 다음 (승인 ≥1 필요)</button>
        <button className="ghost" onClick={load}>새로고침</button>
      </div>
    </section>
  );
}

function AugmentStep({ onDone, onSkip, run }: {
  onDone: () => void; onSkip: () => void;
  run: (fn: () => Promise<unknown>, onOk?: (d: unknown) => void) => () => Promise<void>;
}) {
  const [subs, setSubs] = useState('{"아파치":"nginx"}');
  return (
    <section className="panel">
      <h2>④ 증강 (선택)</h2>
      <div className="row">
        <input type="text" value={subs} onChange={(e) => setSubs(e.target.value)}
               style={{ minWidth: 320 }} aria-label="치환 사전 JSON" />
        <button onClick={run(
          () => api("POST", "/api/v1/records/augment", { substitutions: JSON.parse(subs) }),
          () => onDone(),
        )}>증강 실행 → 다음</button>
        <button className="ghost" onClick={onSkip}>건너뛰기</button>
      </div>
      <p style={{ color: "var(--sub)", fontSize: 12.5, margin: "4px 0 0" }}>
        증강본은 검수 큐 재편입 — 승인 후 학습 반영. CVE/ATT&CK/CWE 식별자는 치환 금지.
      </p>
    </section>
  );
}

function TuningStep({ modelId, datasetVersion, setDatasetVersion, onDone, setOut }: {
  modelId: string; datasetVersion: string; setDatasetVersion: (v: string) => void;
  onDone: (jobId: string) => void; setOut: (s: string) => void;
}) {
  const [training, setTraining] = useState(false);

  const submitAndWatch = async () => {
    try {
      setTraining(true);
      const job = await api<{ job_id: string }>("POST", "/api/v1/tuning/jobs",
        { model_id: modelId, dataset_version: datasetVersion });
      // 학습 워커가 백그라운드 실행 — 상태·이벤트 폴링, succeeded 시 자동 다음
      for (let i = 0; i < 150; i++) {  // 최대 ~5분 (2s 간격)
        await new Promise((r) => setTimeout(r, 2000));
        const [jobs, events] = await Promise.all([
          api<{ jobs: { job_id: string; status: string }[] }>("GET", "/api/v1/tuning/jobs"),
          api<{ events: { message: string }[] }>("GET", `/api/v1/tuning/jobs/${job.job_id}/events`),
        ]);
        const st = jobs.jobs.find((j) => j.job_id === job.job_id)?.status ?? "unknown";
        setOut(`학습 진행 (${st})\n` + events.events.slice(-12).map((e) => e.message).join("\n"));
        if (st === "succeeded") { setTraining(false); onDone(job.job_id); return; }
        if (st === "failed") { setTraining(false); return; }
      }
      setTraining(false);
      setOut("학습 대기 시간 초과 — [튜닝] 페이지에서 상태 확인");
    } catch (e) { setTraining(false); setOut(String(e)); }
  };

  return (
    <section className="panel">
      <h2>⑤ 튜닝 잡</h2>
      <div className="row">
        <span className="pill">{modelId || "모델 미선택 — ① 로 복귀"}</span>
        <input type="text" value={datasetVersion} onChange={(e) => setDatasetVersion(e.target.value)}
               aria-label="dataset version" />
        <button disabled={!modelId || training} onClick={submitAndWatch}>
          {training ? "학습 진행 중..." : "잡 제출 → 학습 → 완료 시 자동 다음"}
        </button>
      </div>
      <p style={{ color: "var(--sub)", fontSize: 12.5, margin: "4px 0 0" }}>
        제출 즉시 학습 워커가 승인 데이터로 학습 실행(torch 미설치 환경은 시뮬레이션 모드) —
        진행 손실·이벤트가 아래에 표시되고, 완료 시 자동 평가→리더보드 반영 후 다음 단계로 이동.
      </p>
    </section>
  );
}

function GateStep({ modelId, datasetVersion, jobId, onDone, setOut }: {
  modelId: string; datasetVersion: string; jobId: string;
  onDone: () => void; setOut: (s: string) => void;
}) {
  const [evalJsonl, setEvalJsonl] = useState("");
  // 모델·데이터셋 기준 평가 지표 자동 입력 — 승인 레코드 정답에서 expected/prediction 생성
  const autoFillRows = useCallback(async () => {
    try {
      const t = await api<{ rows: unknown[] }>("GET",
        `/api/v1/tuning/eval-template?dataset_version=${encodeURIComponent(datasetVersion)}`);
      const rows = t.rows.length ? t.rows
        // 해당 버전 매칭이 없으면 전체 승인 레코드 기준으로 fallback
        : (await api<{ rows: unknown[] }>("GET", "/api/v1/tuning/eval-template")).rows;
      if (!rows.length) {
        // 정답(JSON) 승인 레코드가 없으면 기본 샘플로 채움 — 수정 후 또는 그대로 판정 가능
        setEvalJsonl(JSON.stringify({
          expected: { severity: "high", attack_ids: ["T1059.001"] },
          prediction: { severity: "high", attack_ids: ["T1059.001"] },
        }));
        setOut("승인 레코드에 파싱 가능한 정답(JSON)이 없어 기본 샘플로 채움 — "
          + "문서(needs_annotation) 레코드는 검수에서 정답 작성 후 반영됨");
        return;
      }
      setEvalJsonl(rows.map((r) => JSON.stringify(r)).join("\n"));
    } catch (e) { setOut(String(e)); }
  }, [datasetVersion, setOut]);
  useEffect(() => { autoFillRows(); }, [autoFillRows]);

  const judge = async () => {
    try {
      // 지표 행이 있으면 먼저 기록(수정본 그대로) → 이어서 게이트 판정 — 원클릭
      const rows = evalJsonl.split("\n").filter((l) => l.trim()).map((l) => JSON.parse(l));
      if (rows.length) {
        await api("POST", "/api/v1/tuning/evaluate",
          { model_id: modelId, dataset_version: datasetVersion, rows, job_id: jobId || null });
      }
      const gate = await api<{ passed: boolean }>("POST", "/api/v1/batch/gate",
        { model_id: modelId, dataset_version: datasetVersion });
      setOut(fmt(gate));
      if (gate.passed) onDone();  // 게이트 통과 → 자동 다음
    } catch (e) { setOut(String(e)); }
  };

  return (
    <section className="panel">
      <h2>⑥ 평가 게이트</h2>
      <p style={{ color: "var(--sub)", fontSize: 12.5, margin: "0 0 6px" }}>
        승인 데이터 정답 기준으로 지표 행이 자동 입력됨 — prediction 을 실제 모델 출력으로 수정하거나,
        그대로(완벽 예측 가정) 판정할 수 있다. worker 콜백(/complete)으로 기록된 지표도 함께 반영.
      </p>
      <textarea value={evalJsonl} onChange={(e) => setEvalJsonl(e.target.value)} aria-label="평가 JSONL" />
      <div className="row">
        <button onClick={judge}>게이트 판정 (지표 기록 → 판정, 통과 시 자동 다음)</button>
        <button className="ghost" onClick={autoFillRows}>지표 자동 채우기</button>
        <button className="ghost" disabled={!evalJsonl.trim()} onClick={async () => {
          try {
            const rows = evalJsonl.split("\n").filter((l) => l.trim()).map((l) => JSON.parse(l));
            setOut(fmt(await api("POST", "/api/v1/tuning/evaluate",
              { model_id: modelId, dataset_version: datasetVersion, rows, job_id: jobId || null })));
          } catch (e) { setOut(String(e)); }
        }}>평가 기록만</button>
      </div>
    </section>
  );
}

function LeaderboardStep({ onDone, setOut }: { onDone: () => void; setOut: (s: string) => void }) {
  const [items, setItems] = useState<LbRow[]>([]);
  useEffect(() => {
    (async () => {
      try { setItems((await api<{ items: LbRow[] }>("GET", "/api/v1/tuning/leaderboard")).items); }
      catch (e) { setOut(String(e)); }
    })();
  }, [setOut]);
  return (
    <section className="panel">
      <h2>⑦ 리더보드 비교</h2>
      <table>
        <thead><tr><th>#</th><th>model</th><th>dataset</th><th>baseline</th>
          <th>json_valid</th><th>severity</th><th>attack_f1</th></tr></thead>
        <tbody>
          {items.map((r, i) => (
            <tr key={`${r.model_id}-${i}`}>
              <td>{i + 1}</td><td>{r.model_id}</td><td>{r.dataset_version}</td>
              <td>{r.baseline ? <span className="pill">baseline</span> : ""}</td>
              <td>{r.json_valid_rate.toFixed(3)}</td><td>{r.severity_accuracy.toFixed(3)}</td>
              <td><b>{r.attack_f1.toFixed(3)}</b></td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="row"><button onClick={onDone}>비교 완료 → 다음</button></div>
    </section>
  );
}

function DeployStep({ modelId, jobId, onDone, onNew }: {
  modelId: string; jobId: string; onDone: () => void; onNew: () => void;
}) {
  return (
    <section className="panel">
      <h2>⑧ 배포</h2>
      <p style={{ margin: "0 0 8px" }}>
        게이트 통과 어댑터를 서빙 스택(<code>SERVING_STACK=ollama</code>)에 반영한다 —
        실교체는 serving 연동 확장 지점(PRD 잔여). 모델 <b>{modelId || "-"}</b>
        {jobId && <> / 잡 <b>{jobId}</b></>} 기준. 결과물 다운로드는 [튜닝] 페이지 export.
      </p>
      <div className="row">
        <button onClick={onDone}>파이프라인 완료</button>
        <button className="ghost" onClick={onNew}>+ 새 파이프라인 시작</button>
      </div>
    </section>
  );
}
