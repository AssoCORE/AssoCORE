import "server-only"
import { cookies } from "next/headers"

import { backendFetch } from "@/lib/backend"
import { ACCESS_COOKIE } from "@/lib/auth/cookies"
import type { UserOut } from "@/lib/auth/types"

// GET /user/ is admin-only server-side (require_admin). The (protected)/admin
// layout already redirects non-admins away, so a non-200 here should not
// normally happen — but fail safe rather than throw.
export async function listUsers(): Promise<UserOut[] | null> {
  const store = await cookies()
  const token = store.get(ACCESS_COOKIE)?.value
  if (!token) return null

  const res = await backendFetch("/user/", {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (res.status !== 200) return null
  return res.json()
}
