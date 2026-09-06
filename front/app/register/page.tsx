import Link from "next/link"
import { redirect } from "next/navigation"

import { getCurrentUser } from "@/lib/auth/session"
import { RegisterForm } from "./RegisterForm"

export default async function RegisterPage() {
  const user = await getCurrentUser()
  if (user) redirect("/dashboard")

  return (
    <div className="flex min-h-screen items-center justify-center p-6">
      <div className="flex flex-col items-center gap-4">
        <RegisterForm />
        <p className="text-muted-foreground text-sm">
          Already have an account?{" "}
          <Link href="/login" className="underline underline-offset-4">
            Log in
          </Link>
        </p>
      </div>
    </div>
  )
}
