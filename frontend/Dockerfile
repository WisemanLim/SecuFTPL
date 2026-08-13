# secuftpl-frontend — Next.js (base ≥ node:22 — corepack 최신 pnpm 요구)
FROM node:22-slim
WORKDIR /app
RUN corepack enable
COPY package.json pnpm-workspace.yaml ./
RUN pnpm install || true
COPY . .
RUN pnpm build || true
EXPOSE 3000
# 컨테이너 포트는 3000 고정 — 호스트 노출 포트는 compose 의 ${FRONT_PORT} (SSOT)
CMD ["pnpm", "start", "-p", "3000"]
