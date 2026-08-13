import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Shell from "../components/Shell";

vi.mock("next/navigation", () => ({ usePathname: () => "/rag" }));

describe("Shell", () => {
  beforeEach(() => localStorage.clear());

  it("marks the current route's nav item active and renders children", () => {
    render(
      <Shell>
        <p>content</p>
      </Shell>,
    );
    expect(screen.getByText("content")).toBeInTheDocument();
    const ragLink = screen.getByRole("link", { name: /RAG 업그레이드/ });
    expect(ragLink.className).toContain("active");
    const tuningLink = screen.getByRole("link", { name: /튜닝/ });
    expect(tuningLink.className).not.toContain("active");
  });
});
