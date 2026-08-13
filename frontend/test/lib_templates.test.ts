import { describe, expect, it } from "vitest";
import { buildTemplate, TASK_TYPES } from "../lib/templates";

describe("buildTemplate", () => {
  it("produces a valid canonical record for every known task_type", () => {
    for (const taskType of TASK_TYPES) {
      const rec = JSON.parse(buildTemplate(taskType));
      expect(rec.metadata.task_type).toBe(taskType);
      expect(rec.messages.length).toBeGreaterThanOrEqual(2);
      expect(rec.messages[rec.messages.length - 1].role).toBe("assistant");
      expect(rec.metadata.record_id).toMatch(new RegExp(`^r-${taskType}-`));
    }
  });

  it("falls back to alert_triage for an unknown task_type", () => {
    const known = JSON.parse(buildTemplate("alert_triage"));
    const unknown = JSON.parse(buildTemplate("no_such_task"));
    expect(unknown.messages).toEqual(known.messages);
  });

  it("assistant message content is valid JSON for structured task types", () => {
    for (const taskType of TASK_TYPES.filter((t) => t !== "safety_refusal")) {
      const rec = JSON.parse(buildTemplate(taskType));
      const answer = JSON.parse(rec.messages[rec.messages.length - 1].content);
      expect(answer).toHaveProperty("unknowns");
      expect(answer).toHaveProperty("citations");
    }
  });
});
