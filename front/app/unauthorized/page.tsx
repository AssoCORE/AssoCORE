import Link from "next/link"

export default function UnauthorizedPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 p-6">
      <h1 className="text-2xl font-semibold">403 — You don&apos;t have access to this page</h1>
      <Link href="/" className="underline underline-offset-4">
        Back to dashboard
      </Link>
    </div>
  )
}
