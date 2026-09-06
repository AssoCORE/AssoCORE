// Edge-safe payload decode — no signature verification. This is only used to
// decide whether it's worth attempting a refresh; the backend re-validates
// signature, type and revocation on every real API call regardless.
export interface JwtPayload {
  sub: string
  typ: "access" | "refresh"
  jti: string
  iat: number
  exp: number
  fam?: string
}

export function decodeJwtPayload(token: string): JwtPayload | null {
  try {
    const [, payload] = token.split(".")
    if (!payload) return null
    const base64 = payload.replace(/-/g, "+").replace(/_/g, "/")
    const json = atob(base64)
    return JSON.parse(json) as JwtPayload
  } catch {
    return null
  }
}

export function isExpired(token: string, skewSeconds = 10): boolean {
  const payload = decodeJwtPayload(token)
  if (!payload) return true
  return payload.exp * 1000 <= Date.now() + skewSeconds * 1000
}
