import "server-only";
import { cookies } from "next/headers";

import { backendFetch } from "@/lib/backend";
import { ACCESS_COOKIE } from "@/lib/auth/cookies";
import type { Page, UserOut } from "@/lib/auth/types";

export interface ListUsersOptions {
  /** Case-insensitive search across username, name, firstname and mail. */
  q?: string;
  /** Only users holding this role. */
  role?: string;
  limit?: number;
  offset?: number;
}

// GET /user/ is admin-only server-side (require_admin). The (protected)/admin
// layout already redirects non-admins away, so a non-200 here should not
// normally happen — but fail safe rather than throw.
export async function listUsers(
  options: ListUsersOptions = {}
): Promise<Page<UserOut> | null> {
  const store = await cookies();
  const token = store.get(ACCESS_COOKIE)?.value;
  if (!token) return null;

  const params = new URLSearchParams();
  if (options.q) params.set("q", options.q);
  if (options.role) params.set("role", options.role);
  if (options.limit !== undefined) params.set("limit", String(options.limit));
  if (options.offset !== undefined)
    params.set("offset", String(options.offset));
  const query = params.toString();

  const res = await backendFetch(`/user/${query ? `?${query}` : ""}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (res.status !== 200) return null;
  return res.json();
}
