import { cookies } from "next/headers"

import { backendFetch } from "@/lib/backend"
import {
  ACCESS_COOKIE,
  REFRESH_COOKIE,
  accessCookieOptions,
  refreshCookieOptions,
} from "@/lib/auth/cookies"
import type { TokenPair } from "@/lib/auth/types"

// Reactive safety net for client-side fetches that hit a 401 mid-session,
// after middleware already ran for the current page load. Middleware itself
// handles the proactive case on navigation.
export async function POST() {
  const store = await cookies()
  const refreshToken = store.get(REFRESH_COOKIE)?.value
  if (!refreshToken) {
    return Response.json({ detail: "No session" }, { status: 401 })
  }

  const res = await backendFetch("/user/refresh", {
    method: "POST",
    body: JSON.stringify({ refresh_token: refreshToken }),
  })

  if (res.status === 200) {
    const tokens: TokenPair = await res.json()
    store.set(ACCESS_COOKIE, tokens.access_token, accessCookieOptions(tokens.expires_in))
    store.set(REFRESH_COOKIE, tokens.refresh_token, refreshCookieOptions())
    return Response.json({ ok: true })
  }

  if (res.status === 503) {
    const body = await res.text()
    return new Response(body, {
      status: 503,
      headers: { "Retry-After": res.headers.get("Retry-After") ?? "1" },
    })
  }

  // Truly invalid, expired, or reused — the whole family is dead server-side.
  store.delete(ACCESS_COOKIE)
  store.delete(REFRESH_COOKIE)
  return Response.json({ detail: "Invalid session" }, { status: 401 })
}
