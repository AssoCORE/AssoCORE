import { cookies } from "next/headers"

import { backendFetch } from "@/lib/backend"
import {
  ACCESS_COOKIE,
  REFRESH_COOKIE,
  accessCookieOptions,
  refreshCookieOptions,
} from "@/lib/auth/cookies"
import type { TokenPair } from "@/lib/auth/types"

export async function POST(request: Request) {
  const body = await request.json()
  const res = await backendFetch("/user/login", {
    method: "POST",
    body: JSON.stringify(body),
  })

  if (res.status !== 200) {
    const detail = await res.json().catch(() => ({ detail: "Unknown error" }))
    return Response.json(detail, {
      status: res.status,
      headers: res.headers.get("Retry-After")
        ? { "Retry-After": res.headers.get("Retry-After")! }
        : undefined,
    })
  }

  const tokens: TokenPair = await res.json()
  const store = await cookies()
  store.set(ACCESS_COOKIE, tokens.access_token, accessCookieOptions(tokens.expires_in))
  store.set(REFRESH_COOKIE, tokens.refresh_token, refreshCookieOptions())

  return Response.json({ ok: true })
}
