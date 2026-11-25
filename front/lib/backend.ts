import "server-only";
import { headers } from "next/headers";

// Server-only: the browser never calls FastAPI directly, only same-origin
// Next.js routes. This keeps the backend off browser CORS entirely, since a
// server-to-server fetch isn't subject to it.
export const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

// Shared with the backend (k8s `bff-secret`, compose `.env`). Proves to its rate
// limiter that X-Client-IP really comes from this server: see
// back/app/core/rate_limit.py. Unset, nothing is forwarded and every user
// shares this server's rate-limit bucket.
const BFF_SHARED_SECRET = process.env.BFF_SHARED_SECRET;

/**
 * The browser's IP, as seen by the hop in front of this server.
 *
 * The *last* X-Forwarded-For entry is the one written by whoever connected to
 * us: Traefik in k8s (which, trusting no upstream forwarded headers, replaces
 * any value the client sent), or Next.js itself in dev (it fills the header from
 * the socket when it is absent). Earlier entries come from the client and can be
 * forged, so they are never used.
 */
export function clientIpFrom(incoming: Headers): string | undefined {
  const last = incoming.get("x-forwarded-for")?.split(",").at(-1)?.trim();
  return last || undefined;
}

/** The headers that carry the browser's IP to the backend's rate limiter. */
export function forwardingHeaders(incoming: Headers): Record<string, string> {
  const ip = clientIpFrom(incoming);
  if (!BFF_SHARED_SECRET || !ip) return {};
  return { "X-Client-IP": ip, "X-BFF-Secret": BFF_SHARED_SECRET };
}

async function currentForwardingHeaders(): Promise<Record<string, string>> {
  try {
    return forwardingHeaders(await headers());
  } catch {
    // Called outside a request (build-time rendering): there is no browser.
    return {};
  }
}

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
      ...(await currentForwardingHeaders()),
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });
}
