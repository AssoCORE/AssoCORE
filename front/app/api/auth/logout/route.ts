import { cookies } from "next/headers"

import { backendFetch } from "@/lib/backend"
import { ACCESS_COOKIE, REFRESH_COOKIE } from "@/lib/auth/cookies"

export async function POST() {
  const store = await cookies()
  const access = store.get(ACCESS_COOKIE)?.value
  const refresh = store.get(REFRESH_COOKIE)?.value

  if (access) {
    await backendFetch("/user/logout", {
      method: "POST",
      headers: { Authorization: `Bearer ${access}` },
      body: JSON.stringify({ refresh_token: refresh ?? null }),
    }).catch(() => undefined)
  }

  // The user's intent is to leave either way — clear cookies regardless of
  // what the backend reported (already-revoked token, redis hiccup, etc).
  store.delete(ACCESS_COOKIE)
  store.delete(REFRESH_COOKIE)

  return new Response(null, { status: 204 })
}
