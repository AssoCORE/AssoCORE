"use client"

import { createContext, useContext, type ReactNode } from "react"

import type { UserOut } from "@/lib/auth/types"

const AuthContext = createContext<UserOut | null>(null)

export function AuthProvider({
  user,
  children,
}: {
  user: UserOut
  children: ReactNode
}) {
  return <AuthContext.Provider value={user}>{children}</AuthContext.Provider>
}

export function useAuth(): UserOut {
  const user = useContext(AuthContext)
  if (!user) {
    throw new Error("useAuth must be used within <AuthProvider>")
  }
  return user
}
