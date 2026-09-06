import { backendFetch } from "@/lib/backend"

// Forwards to POST /user/ verbatim. No auto-login — the client redirects to
// /login on success and lets the normal login flow set cookies.
export async function POST(request: Request) {
  const body = await request.json()
  const res = await backendFetch("/user/", {
    method: "POST",
    body: JSON.stringify(body),
  })

  const data = await res.json().catch(() => ({}))
  return Response.json(data, { status: res.status })
}
