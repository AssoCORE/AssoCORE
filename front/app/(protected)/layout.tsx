import Link from "next/link"
import { redirect } from "next/navigation"

import { getCurrentUser } from "@/lib/auth/session"
import { isAdmin } from "@/lib/auth/roles"
import { AuthProvider } from "@/components/auth/AuthProvider"
import { LogoutButton } from "@/components/auth/LogoutButton"

export default async function ProtectedLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const user = await getCurrentUser()
  if (!user) redirect("/login")

  return (
    <AuthProvider user={user}>
      <div className="flex min-h-screen flex-col">
        <header className="flex items-center justify-between border-b p-4">
          <nav className="flex items-center gap-4 text-sm">
            <Link href="/dashboard">Dashboard</Link>
            {isAdmin(user) && <Link href="/admin">Admin</Link>}
          </nav>
          <div className="flex items-center gap-3 text-sm">
            <span>
              {user.firstname} {user.name} ({user.roles.map((r) => r.name).join(", ") || "no roles"})
            </span>
            <LogoutButton />
          </div>
        </header>
        <main className="flex-1 p-6">{children}</main>
      </div>
    </AuthProvider>
  )
}
