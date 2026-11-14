import "server-only";
import { cookies } from "next/headers";

import { backendFetch } from "@/lib/backend";
import { ACCESS_COOKIE } from "@/lib/auth/cookies";
import type { Page, UserOut } from "@/lib/auth/types";
import type { PeopleById } from "@/lib/types";

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

/**
 * Names of every user by id, for an admin's participant lists — null for anyone
 * else, since GET /user/ is admin-only. Only display fields are kept: UserOut also
 * carries each user's notifications and reminders, which must not reach the client.
 */
export async function peopleById(): Promise<PeopleById | undefined> {
  const page = await listUsers({ limit: 200 });
  if (!page) return undefined;
  return Object.fromEntries(
    page.items.map((u) => [u.id, { firstname: u.firstname, name: u.name, username: u.username }])
  );
}
