/** @type {import('next').NextConfig} */
const nextConfig = {
  // 백엔드 프록시 — 브라우저는 same-origin /api/* 호출, CORS 불필요 (포트는 .env SSOT)
  async rewrites() {
    const api = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";
    return [{ source: "/api/:path*", destination: `${api}/api/:path*` }];
  },
};

export default nextConfig;
