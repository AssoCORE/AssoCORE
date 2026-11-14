import "server-only";
import { cookies } from "next/headers";

import { ACCESS_COOKIE } from "@/lib/auth/cookies";
import { BackendError, backendFetch } from "@/lib/backend";

/**
 * Authenticated server-to-server call to FastAPI with the caller's access token.
 *
 * Usable from Server Components, Route Handlers and Server Actions. Token refresh
 * is not handled here: `proxy.ts` already refreshed it before this request reached us.
 */
export async function apiFetch(path: string, init?: RequestInit): Promise<Response> {
  const store = await cookies();
  const token = store.get(ACCESS_COOKIE)?.value;
  return backendFetch(path, {
    ...init,
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init?.headers ?? {}),
    },
  });
}

/** Like `apiFetch`, but parses JSON and throws `BackendError` on any non-2xx. */
export async function apiJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await apiFetch(path, init);
  if (!res.ok) throw new BackendError(res.status, await readDetail(res));
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

/** FastAPI's `detail` is a string, or a list of validation errors on a 422. */
export async function readDetail(res: Response): Promise<string> {
  try {
    const body = await res.json();
    const detail = body?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail
        .map((d: { loc?: unknown[]; msg?: string }) =>
          [d.loc?.slice(1).join("."), d.msg].filter(Boolean).join(" : "),
        )
        .join(" ; ");
    }
  } catch {
    // not JSON
  }
  return res.statusText || `Erreur ${res.status}`;
}

export function query(params: Record<string, string | number | boolean | undefined | null>) {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "" || value === false) continue;
    search.set(key, String(value));
  }
  const s = search.toString();
  return s ? `?${s}` : "";
}

export type ActionResult = { ok: true } | { ok: false; error: string };

/** Turns a thrown error into a result a Client Component can display. */
export function toActionError(err: unknown): ActionResult {
  if (err instanceof BackendError) {
    if (err.status === 401) return { ok: false, error: "Session expirée, reconnectez-vous." };
    if (err.status === 403) return { ok: false, error: "Action non autorisée." };
    return { ok: false, error: err.detail };
  }
  return { ok: false, error: "Service indisponible, réessayez plus tard." };
}
