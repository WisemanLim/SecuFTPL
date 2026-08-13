// SecuFTPL frontend — API helper (rewrites 로 same-origin /api/* → FastAPI 프록시)
export async function api<T = unknown>(
  method: "GET" | "POST" | "DELETE",
  path: string,
  body?: unknown,
): Promise<T> {
  const res = await fetch(path, {
    method,
    headers: { "content-type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
    cache: "no-store",
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(`${res.status} ${JSON.stringify(data)}`);
  return data as T;
}

export const fmt = (obj: unknown) => JSON.stringify(obj, null, 2);

// 시간 표기 원칙(PRD): API 는 UTC ISO8601 — 화면은 브라우저 locale 로 변환해 표시.
export const toLocale = (iso: string | null | undefined) =>
  iso ? new Date(iso).toLocaleString() : "-";
