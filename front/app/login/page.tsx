import Link from "next/link"
import { redirect } from "next/navigation"

import { getCurrentUser } from "@/lib/auth/session"
import { LoginForm } from "./LoginForm"

export default async function LoginPage() {
  const user = await getCurrentUser()
  if (user) redirect("/dashboard")

  return (
    <div className="flex min-h-screen items-center justify-center p-6">
      <div className="flex flex-col items-center gap-4">
        <LoginForm />
        <p className="text-muted-foreground text-sm">
          No account?{" "}
          <Link href="/register" className="underline underline-offset-4">
            Register
          </Link>
        </p>
      </div>
    </div>
  )
}
