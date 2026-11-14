import { readDetail } from "@/lib/api"
import { backendFetch } from "@/lib/backend"

// Forwards to POST /user/. No auto-login — the client redirects to /login on
// success and lets the normal login flow set cookies.
export async function POST(request: Request) {
  const body = await request.json()
  const res = await backendFetch("/user/", {
    method: "POST",
    body: JSON.stringify(body),
  })

  // A 422's `detail` is a list of validation errors, not a string; flatten it
  // so the form can render it as-is.
  if (!res.ok) {
    return Response.json({ detail: await readDetail(res) }, { status: res.status })
  }
  const data = await res.json().catch(() => ({}))
  return Response.json(data, { status: res.status })
}
