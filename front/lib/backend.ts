import "server-only";

// Server-only: the browser never calls FastAPI directly, only same-origin
// Next.js routes. This keeps the backend off browser CORS entirely, since a
// server-to-server fetch isn't subject to it.
export const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

export class BackendError extends Error {
  constructor(
    public status: number,
    public detail: string
  ) {
    super(detail);
  }
}

export async function backendFetch(
  path: string,
  init?: RequestInit
): Promise<Response> {
  // A FormData body must let fetch set its own multipart boundary header.
  const json = !(init?.body instanceof FormData);
  return fetch(`${BACKEND_URL}${path}`, {
    ...init,
    headers: {
      ...(json ? { "Content-Type": "application/json" } : {}),
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });
}
