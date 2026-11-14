import { redirect } from "next/navigation"

import { AuthProvider } from "@/components/auth/AuthProvider"
import { AppShell } from "@/components/custom/app-shell"
import { apiJson } from "@/lib/api"
import { getCurrentUser } from "@/lib/auth/session"
import type { NotificationOut, Page } from "@/lib/types"

export default async function ProtectedLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const user = await getCurrentUser()
  if (!user) redirect("/login")

  // Newest first, and the unread count from `total` — as the backend documents.
  const [latest, unread] = await Promise.all([
    apiJson<Page<NotificationOut>>("/user/notification/?limit=8").catch(() => null),
    apiJson<Page<NotificationOut>>("/user/notification/?unread_only=true&limit=1").catch(
      () => null
    ),
  ])

  return (
    <AuthProvider user={user}>
      <AppShell notifications={latest?.items ?? []} unreadCount={unread?.total ?? 0}>
        {children}
      </AppShell>
    </AuthProvider>
  )
}
