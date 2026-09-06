import type { Role } from "@/lib/auth/types"

// Mirrors back/app/core/roles.py — keep in sync.
export const ROLE_ADMIN = "admin"
export const ROLE_STAFF = "staff"
export const ROLE_MEMBER = "member"

export function hasRole(user: { roles: Role[] }, ...names: string[]): boolean {
  return user.roles.some((r) => names.includes(r.name))
}

export function isAdmin(user: { roles: Role[] }): boolean {
  return hasRole(user, ROLE_ADMIN)
}
