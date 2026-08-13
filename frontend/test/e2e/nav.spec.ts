import { expect, test } from "@playwright/test";

// 사이드바 내비게이션 스모크 — 백엔드 미기동 상태에서도 페이지 셸·라우팅이 동작해야 함.
test("sidebar navigates between pages and highlights the active route", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("link", { name: "튜닝" })).toBeVisible();

  await page.getByRole("link", { name: "튜닝" }).click();
  await expect(page).toHaveURL(/\/tuning$/);
  await expect(page.getByRole("link", { name: "튜닝" })).toHaveClass(/active/);

  await page.getByRole("link", { name: "RAG 업그레이드" }).click();
  await expect(page).toHaveURL(/\/rag$/);
  await expect(page.getByRole("heading", { name: /RAG 코퍼스/ })).toBeVisible();
});

test("sidebar collapse toggle persists across reload", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: /사이드바 접기/ }).click();
  await expect(page.getByText("SecuFTPL")).toHaveCount(0);
  await page.reload();
  await expect(page.getByText("SecuFTPL")).toHaveCount(0);
});
