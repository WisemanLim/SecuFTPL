"use client";
// 대시보드 — 파이프라인 현황 요약 (PRD E7)
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type Counts = { models: number; pinned: number; pending: number; approved: number;
                jobs: number; evals: number; upRatio: number | null };

export default function Dashboard() {
  const [counts, setCounts] = useState<Counts | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const [models, pinned, pending, approved, jobs, lb, stats] = await Promise.all([
          api<{ count: number }>("GET", "/api/v1/models"),
          api<{ count: number }>("GET", "/api/v1/models?status=pinned"),
          api<{ count: number }>("GET", "/api/v1/records/queue?state=pending"),
          api<{ count: number }>("GET", "/api/v1/records/queue?state=approved"),
          api<{ count: number }>("GET", "/api/v1/tuning/jobs"),
          api<{ count: number }>("GET", "/api/v1/tuning/leaderboard"),
          api<{ up_ratio: number | null }>("GET", "/api/v1/feedback/stats"),
        ]);
        setCounts({ models: models.count, pinned: pinned.count, pending: pending.count,
                    approved: approved.count, jobs: jobs.count, evals: lb.count,
                    upRatio: stats.up_ratio });
      } catch (e) { setError(String(e)); }
    })();
  }, []);

  return (
    <>
      <section className="panel">
        <h2>파이프라인 현황</h2>
        {error && <pre className="out">{error} — 백엔드(make dev) 기동 확인</pre>}
        <div className="cards">
          <div className="card"><div className="num">{counts?.models ?? "–"}</div><div className="label">등록 모델 (pinned {counts?.pinned ?? "–"})</div></div>
          <div className="card"><div className="num">{counts?.pending ?? "–"}</div><div className="label">검수 대기</div></div>
          <div className="card"><div className="num">{counts?.approved ?? "–"}</div><div className="label">승인 레코드 (학습 가능)</div></div>
          <div className="card"><div className="num">{counts?.jobs ?? "–"}</div><div className="label">튜닝 잡</div></div>
          <div className="card"><div className="num">{counts?.evals ?? "–"}</div><div className="label">평가 결과</div></div>
          <div className="card"><div className="num">{counts?.upRatio == null ? "–" : `${Math.round(counts.upRatio * 100)}%`}</div><div className="label">만족도(up 비율)</div></div>
        </div>
      </section>
      <section className="panel">
        <h2>파이프라인 흐름</h2>
        <p style={{ color: "var(--sub)", margin: "0 0 10px" }}>
          모델 선택 → 데이터셋 수집(게이트·가명화·중복제거) → 검수 승인 → (증강) → 튜닝 잡 →
          평가 게이트 → 리더보드 비교 → 배포 — 단계 완료 시 자동으로 다음 단계로 이동한다.
        </p>
        <a href="/pipeline"><button>파이프라인 시작 →</button></a>
      </section>
    </>
  );
}
