import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// 시험 표준(test-runner 스킬): frontend 프로파일 = Vitest(단위) + Playwright(e2e)
export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    setupFiles: ["./test/setup.ts"],
    include: ["test/**/*.test.{ts,tsx}"],
    exclude: ["test/e2e/**"],
  },
  resolve: {
    alias: { "@": import.meta.dirname },
  },
});
