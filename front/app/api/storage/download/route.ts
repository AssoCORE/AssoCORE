import { apiFetch, query, readDetail } from "@/lib/api"

// Streams GET /storage/download through Next.js so the browser gets the file
// without ever holding the access token.
export async function GET(request: Request) {
  const path = new URL(request.url).searchParams.get("path")
  if (!path) return Response.json({ detail: "path is required" }, { status: 400 })

  const res = await apiFetch(`/storage/download${query({ path })}`)
  if (!res.ok || !res.body) {
    return Response.json({ detail: await readDetail(res) }, { status: res.status })
  }

  return new Response(res.body, {
    headers: {
      "Content-Type": res.headers.get("Content-Type") ?? "application/octet-stream",
      "Content-Disposition":
        res.headers.get("Content-Disposition") ??
        `attachment; filename="${path.split("/").pop()}"`,
    },
  })
}
