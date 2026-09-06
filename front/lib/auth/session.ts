import "server-only"
import { cache } from "react"
import { cookies } from "next/headers"

import { backendFetch } from "@/lib/backend"
import { ACCESS_COOKIE } from "@/lib/auth/cookies"
import type { UserOut } from "@/lib/auth/types"

// Does NOT attempt a refresh itself — that's middleware's job, which runs
// before any Server Component in this tree. cache() dedupes the /user/me
// call across nested layouts/pages within the same request.
export const getCurrentUser = cache(async (): Promise<UserOut | null> => {
  const store = await cookies()
  const token = store.get(ACCESS_COOKIE)?.value
  if (!token) return null

  const res = await backendFetch("/user/me", {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (res.status !== 200) return null
  return res.json()
})
