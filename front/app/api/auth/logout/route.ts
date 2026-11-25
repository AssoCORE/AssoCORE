import { cookies } from "next/headers";
import { ACCESS_COOKIE, REFRESH_COOKIE } from "@/lib/auth/cookies";
import { backendFetch } from "@/lib/backend";

// `?all=1` logs out everywhere (POST /user/logout/all): every refresh-token
// family of the user is killed, not just this browser's.
export async function POST(request: Request) {
  const everywhere = new URL(request.url).searchParams.get("all") === "1";
  const store = await cookies();
  const access = store.get(ACCESS_COOKIE)?.value;
  const refresh = store.get(REFRESH_COOKIE)?.value;

  let failed = false;
  if (access) {
    const res = await backendFetch(
      everywhere ? "/user/logout/all" : "/user/logout",
      {
        method: "POST",
        headers: { Authorization: `Bearer ${access}` },
        body: everywhere
          ? undefined
          : JSON.stringify({ refresh_token: refresh ?? null }),
      }
    ).catch(() => null);
    failed = !res?.ok;
  }

  // A plain logout clears cookies regardless of what the backend reported
  // (already-revoked token, redis hiccup, etc) — the user's intent is to leave.
  // "Everywhere" must not pretend: if other sessions were not revoked, say so
  // and keep this one.
  if (everywhere && failed) {
    return Response.json(
      {
        detail:
          "Impossible de fermer les autres sessions, réessayez plus tard.",
      },
      { status: 503 }
    );
  }

  store.delete(ACCESS_COOKIE);
  store.delete(REFRESH_COOKIE);

  return new Response(null, { status: 204 });
}
