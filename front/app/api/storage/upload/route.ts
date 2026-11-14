import { apiFetch, query, readDetail } from "@/lib/api";

// Relays a multipart upload to POST /storage/upload. A Route Handler rather than a
// Server Action: actions cap their body at 1 MB, files routinely exceed that.
export async function POST(request: Request) {
  const dir = (new URL(request.url).searchParams.get("dir") ?? "").replace(/^\/+|\/+$/g, "");

  let form: FormData;
  try {
    form = await request.formData();
  } catch {
    return Response.json({ detail: "Corps multipart invalide." }, { status: 400 });
  }
  const file = form.get("file");
  if (!(file instanceof File) || !file.name) {
    return Response.json({ detail: "Aucun fichier reçu." }, { status: 400 });
  }

  const path = [dir, file.name].filter(Boolean).join("/");

  // Never overwrite. The backend's own `overwrite=false` check answers 404 for a
  // file that does not exist yet (nc-py-api's by_path raises instead of returning
  // None), so check existence here: 200 means taken, 404 means free.
  const existing = await apiFetch(`/storage/info${query({ path })}`);
  if (existing.ok) {
    return Response.json({ detail: `« ${file.name} » existe déjà.` }, { status: 409 });
  }
  if (existing.status !== 404) {
    return Response.json({ detail: await readDetail(existing) }, { status: existing.status });
  }

  const body = new FormData();
  body.set("file", file, file.name);
  const res = await apiFetch(`/storage/upload${query({ path })}`, { method: "POST", body });
  if (!res.ok) {
    return Response.json({ detail: await readDetail(res) }, { status: res.status });
  }
  return Response.json(await res.json(), { status: 201 });
}
