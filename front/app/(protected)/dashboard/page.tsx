import { getCurrentUser } from "@/lib/auth/session"

export default async function DashboardPage() {
  const user = await getCurrentUser()

  return (
    <div className="space-y-2">
      <h1 className="text-2xl font-semibold">Welcome, {user?.firstname}</h1>
      <p className="text-muted-foreground">
        Logged in as <span className="font-mono">{user?.username}</span> ({user?.mail})
      </p>
    </div>
  )
}
