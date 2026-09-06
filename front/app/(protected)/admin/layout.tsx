import { redirect } from "next/navigation"

import { getCurrentUser } from "@/lib/auth/session"
import { isAdmin } from "@/lib/auth/roles"

export default async function AdminLayout({
  children,
}: {
  children: React.ReactNode
}) {
  // getCurrentUser() is wrapped in React's cache(), so this dedupes against
  // the call the parent (protected) layout already made in this request.
  const user = await getCurrentUser()
  if (!user || !isAdmin(user)) redirect("/unauthorized")

  return <>{children}</>
}
