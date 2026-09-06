export const ACCESS_COOKIE = "access_token"
export const REFRESH_COOKIE = "refresh_token"

// Both cookies use path "/" — a refresh_token scoped to a narrower path (e.g.
// "/api/auth") would never be attached by the browser to a plain page
// navigation, so middleware would never see it and would treat every valid
// session as logged-out.
export function accessCookieOptions(maxAgeSeconds: number) {
  return {
    httpOnly: true,
    sameSite: "lax" as const,
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: maxAgeSeconds,
  }
}

export function refreshCookieOptions() {
  return {
    httpOnly: true,
    sameSite: "lax" as const,
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: 60 * 60 * 24 * 30, // 30 days — matches the backend's REFRESH_TOKEN_EXPIRE_DAYS default
  }
}
