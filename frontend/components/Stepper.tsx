"use client";
// 파이프라인 스테퍼 — 단계 카드 + 상태 (PRD §7.11, LLM Development Stages 카드 레이아웃 참고)
export type StepStatus = "done" | "current" | "pending" | "skipped";
export type StepDef = { id: string; title: string; desc: string };

const STATUS_LABEL: Record<StepStatus, string> = {
  done: "완료", current: "진행 중", pending: "대기", skipped: "건너뜀",
};

export default function Stepper({ steps, statuses, onNavigate }: {
  steps: StepDef[];
  statuses: StepStatus[];
  onNavigate: (idx: number) => void;  // 이전(완료/건너뜀) 단계만 복귀 허용
}) {
  return (
    <div className="stepper" role="list" aria-label="파이프라인 단계">
      {steps.map((s, i) => {
        const st = statuses[i];
        const navigable = st === "done" || st === "skipped";
        return (
          <button key={s.id} role="listitem" type="button"
                  className={`step-card ${st}${navigable ? " navigable" : ""}`}
                  disabled={!navigable && st !== "current"}
                  onClick={() => navigable && onNavigate(i)}
                  aria-current={st === "current" ? "step" : undefined}
                  title={navigable ? `${s.title} 단계로 돌아가기` : s.title}>
            <div className="head">
              <span>{i + 1}. {s.title}</span>
              <span className="status">{STATUS_LABEL[st]}</span>
            </div>
            <div className="body">{s.desc}</div>
          </button>
        );
      })}
    </div>
  );
}
