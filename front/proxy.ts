import { NextRequest, NextResponse } from "next/server"

import { BACKEND_URL } from "@/lib/backend"
import {
  ACCESS_COOKIE,
  REFRESH_COOKIE,
  accessCookieOptions,
  refreshCookieOptions,
} from "@/lib/auth/cookies"
import { isExpired } from "@/lib/auth/jwt"

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico|login|register).*)"],
}

async function callRefresh(refreshToken: string) {
  return fetch(`${BACKEND_URL}/user/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  })
}

export async function proxy(request: NextRequest) {
  const access = request.cookies.get(ACCESS_COOKIE)?.value
  const refresh = request.cookies.get(REFRESH_COOKIE)?.value

  const needsRefresh = !access || isExpired(access)
  if (!needsRefresh) {
    return NextResponse.next()
  }

  if (!refresh) {
    return NextResponse.redirect(new URL("/login", request.url))
  }

  let res = await callRefresh(refresh)
  if (res.status === 503) {
    const retryAfter = Number(res.headers.get("Retry-After") ?? "1")
    await new Promise((resolve) => setTimeout(resolve, retryAfter * 1000))
    res = await callRefresh(refresh)
  }

  if (res.status !== 200) {
    const redirectRes = NextResponse.redirect(new URL("/login", request.url))
    redirectRes.cookies.delete(ACCESS_COOKIE)
    redirectRes.cookies.delete(REFRESH_COOKIE)
    return redirectRes
  }

  const tokens = await res.json()

  // Mutate request cookies BEFORE constructing the response so the Server
  // Component render that follows sees the new access token in this same pass.
  request.cookies.set(ACCESS_COOKIE, tokens.access_token)
  const response = NextResponse.next({ request })
  response.cookies.set(
    ACCESS_COOKIE,
    tokens.access_token,
    accessCookieOptions(tokens.expires_in)
  )
  response.cookies.set(REFRESH_COOKIE, tokens.refresh_token, refreshCookieOptions())
  return response
}
