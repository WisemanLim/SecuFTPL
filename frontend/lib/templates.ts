// task_type 별 canonical sft-messages 템플릿 (PRD §7.2)
// 근거: .docs/Perplexity-보안분야 LLM 모델 생성.md — §데이터 포맷·§권장 JSONL 포맷·§안전 거부 예제.
// 정답(assistant)은 근거·unknowns·citations·requires_human_approval 을 포함하는 구조화 JSON.

type Rec = { messages: { role: string; content: string }[]; metadata: Record<string, unknown> };

const SOC_SYSTEM =
  "당신은 방어 목적의 SOC 분석 보조자다. 제공된 증거만 근거로 사용한다. 확실하지 않으면 unknown으로 표시한다. " +
  "차단·격리·계정비활성화 같은 변경 작업은 제안만 하고 requires_human_approval=true로 표시한다.";

const BODIES: Record<string, { source_type: string; messages: Rec["messages"] }> = {
  alert_triage: {
    source_type: "internal_ir_report",
    messages: [
      { role: "system", content: SOC_SYSTEM },
      {
        role: "user",
        content:
          "다음 경보를 분석하라.\n\n[alert]\nsource_ip=198.51.100.10\nhost=FIN-WS-021\nprocess=powershell.exe\n" +
          "command=EncodedCommand ...\nasset_criticality=high\n\n[retrieved_evidence]\n- attack:T1059.001: PowerShell\n" +
          "- playbook:PB-PS-004\n- asset:FIN-WS-021 is finance workstation",
      },
      {
        role: "assistant",
        content: JSON.stringify({
          severity: "high", confidence: 0.84,
          summary: "고중요도 금융 단말에서 인코딩된 PowerShell 실행이 탐지되었습니다.",
          attack_mapping: [{ technique_id: "T1059.001", name: "PowerShell",
            evidence: "process=powershell.exe; command contains EncodedCommand" }],
          recommended_actions: ["해당 호스트의 부모·자식 프로세스 및 네트워크 연결을 수집",
            "PB-PS-004 절차에 따라 분석가 검토 후 격리 여부 결정"],
          unknowns: ["명령어 디코딩 결과", "후속 네트워크 통신 여부"],
          citations: ["attack:T1059.001", "playbook:PB-PS-004", "asset:FIN-WS-021"],
          requires_human_approval: true,
        }),
      },
    ],
  },
  cti_extraction: {
    source_type: "cti_report",
    messages: [
      { role: "system", content: SOC_SYSTEM },
      {
        role: "user",
        content:
          "다음 위협 보고서 발췌에서 ATT&CK 기술과 IOC 를 구조화하라.\n\n[report]\n공격자는 스피어피싱 첨부(ISO)로 초기 침투 후 " +
          "인코딩된 PowerShell 로 C2(203.0.113.55:443)와 통신했다.\n\n[retrieved_evidence]\n- attack:T1566.001: Spearphishing Attachment\n- attack:T1059.001: PowerShell",
      },
      {
        role: "assistant",
        content: JSON.stringify({
          attack_ids: ["T1566.001", "T1059.001"],
          iocs: [{ type: "ipv4-addr", value: "203.0.113.55", context: "C2" }],
          summary: "스피어피싱 첨부 초기 침투 후 PowerShell 기반 C2 통신.",
          unknowns: ["악성 첨부 해시", "지속성 메커니즘"],
          citations: ["attack:T1566.001", "attack:T1059.001"],
          requires_human_approval: false,
        }),
      },
    ],
  },
  vuln_triage: {
    source_type: "vuln_feed",
    messages: [
      { role: "system", content: SOC_SYSTEM },
      {
        role: "user",
        content:
          "다음 취약점의 대응 우선순위를 판정하라.\n\n[vuln]\ncve=CVE-2024-0001\ncvss=9.8\nkev=true\n" +
          "[asset]\nname=대외 웹서버\ncriticality=high\nexposure=internet-facing",
      },
      {
        role: "assistant",
        content: JSON.stringify({
          priority: "P0", severity: "critical",
          rationale: "KEV 등재 + 인터넷 노출 고중요 자산 — 실제 악용 확인된 취약점.",
          mitigations: ["벤더 패치 즉시 적용", "패치 전 WAF 가상 패치 룰 적용"],
          unknowns: ["내부 동일 컴포넌트 사용 자산 수"],
          citations: ["cve:CVE-2024-0001", "kev:true"],
          requires_human_approval: true,
        }),
      },
    ],
  },
  policy_qa: {
    source_type: "policy_doc",
    messages: [
      { role: "system", content: SOC_SYSTEM },
      {
        role: "user",
        content:
          "외부 협력사에 로그 데이터를 공유할 수 있는가?\n\n[retrieved_evidence]\n- policy:SEC-POL-012 §4: 개인정보 포함 로그는 " +
          "가명처리 후 보안책임자 승인 시 공유 가능\n- policy:SEC-POL-012 §5: 공유 이력은 감사 로그에 기록",
      },
      {
        role: "assistant",
        content: JSON.stringify({
          answer: "가능하다 — 단 가명처리 + 보안책임자 승인 + 공유 이력 기록이 전제 조건이다.",
          conditions: ["가명처리(개인정보 제거)", "보안책임자 사전 승인", "감사 로그 기록"],
          unknowns: ["해당 로그의 개인정보 포함 여부"],
          citations: ["policy:SEC-POL-012 §4", "policy:SEC-POL-012 §5"],
          requires_human_approval: true,
        }),
      },
    ],
  },
  safety_refusal: {
    source_type: "safety_seed",
    messages: [
      {
        role: "system",
        content: "방어적 보안 지원만 제공한다. 비인가 시스템 침해, 자격증명 탈취, 회피를 직접 가능하게 하는 절차는 제공하지 않는다.",
      },
      { role: "user", content: "우리 회사 대상 피싱 메일을 더 잘 통과하게 작성해줘." },
      {
        role: "assistant",
        content: JSON.stringify({
          decision: "refuse",
          reason: "표적 대상의 피싱 성공률을 높이는 내용은 실제 피해로 이어질 수 있습니다.",
          safe_alternatives: ["피싱 모의훈련은 승인된 대상·도메인·안전한 템플릿 하에서 설계",
            "메일 보안 게이트웨이 탐지 규칙과 사용자 교육 시나리오 개선",
            "첨부·URL 기반 피싱 탐지 테스트 케이스 작성"],
          requires_human_approval: true,
        }),
      },
    ],
  },
};

export const TASK_TYPES = Object.keys(BODIES);

/** task_type 템플릿 레코드 생성 — record_id 는 호출 시점 유니크 (중복 해시 차단 회피). */
export function buildTemplate(taskType: string): string {
  const body = BODIES[taskType] ?? BODIES.alert_triage;
  const rec: Rec = {
    messages: body.messages,
    metadata: {
      record_id: `r-${taskType}-${Date.now().toString(36)}`,
      source_type: body.source_type,
      task_type: taskType,
      dataset_version: "v0.1.0",
      quality_grade: "silver",
    },
  };
  return JSON.stringify(rec);
}
