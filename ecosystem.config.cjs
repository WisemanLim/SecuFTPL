// secuftpl — PM2 process manager (기본 멀티프로세스 매니저)
// 실행: make local-all  (= ENV_FILE=.env.local npx pm2 start ecosystem.config.cjs)
// Node/npx 필요. 대안: PROC_MGR=honcho make local-all (Procfile.dev 사용).
// 포트/IP 는 .env.* SSOT (PRD §7.9) — ENV_FILE 을 파싱해 API_PORT/BIND_HOST/FRONT_PORT 를 읽는다. 하드코딩 금지.
const { readFileSync } = require('node:fs');

function loadEnv(path) {
  const env = {};
  try {
    for (const line of readFileSync(path, 'utf8').split('\n')) {
      const m = line.match(/^([A-Za-z_]\w*)=(.*)$/);
      if (m) env[m[1]] = m[2].split('#')[0].trim();
    }
  } catch { /* env 파일 없으면 기본값 사용 */ }
  return env;
}

const env = loadEnv(process.env.ENV_FILE || '.env.local');
const host = env.BIND_HOST || '127.0.0.1';
const port = env.API_PORT || '8000';
const frontPort = env.FRONT_PORT || '3000';

module.exports = {
  apps: [
    {
      name: 'secuftpl-web',
      script: 'uv',
      args: `run uvicorn app.main:app --reload --host ${host} --port ${port}`,
      interpreter: 'none',
    },
    {
      // E7 독립 frontend — web 과 함께 일괄 기동 (make local-all)
      name: 'secuftpl-front',
      cwd: './frontend',
      script: 'pnpm',
      args: `dev -p ${frontPort}`,
      interpreter: 'none',
      env: { NEXT_PUBLIC_API_BASE: `http://${host}:${port}` },
    },
    // 워커 예시(필요 시 주석 해제 — arq/celery/rq 등):
    // { name: 'secuftpl-worker', script: 'uv', args: 'run python -m app.worker', interpreter: 'none' },
  ],
};
