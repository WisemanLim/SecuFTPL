import { describe, expect, it } from "vitest";
import { fmt, toLocale } from "../lib/api";

describe("fmt", () => {
  it("pretty-prints objects with 2-space indent", () => {
    expect(fmt({ a: 1, b: [1, 2] })).toBe(JSON.stringify({ a: 1, b: [1, 2] }, null, 2));
  });
});

describe("toLocale", () => {
  it("converts an ISO8601 UTC string to a locale string", () => {
    const iso = "2026-08-13T00:00:00+00:00";
    expect(toLocale(iso)).toBe(new Date(iso).toLocaleString());
  });

  it("returns '-' for null/undefined (PRD 시간 표기 원칙: 값 없음 처리)", () => {
    expect(toLocale(null)).toBe("-");
    expect(toLocale(undefined)).toBe("-");
  });
});
