"use server";

import { revalidatePath } from "next/cache";
import { cookies } from "next/headers";

import { type ActionResult, apiJson, query, toActionError } from "@/lib/api";
import { ACCESS_COOKIE, REFRESH_COOKIE } from "@/lib/auth/cookies";
import type {
  EventOut,
  NcLinkInit,
  NcLinkPoll,
  StorageNode,
} from "@/lib/types";

// Server Actions: they run on the Next.js server, so they read the httpOnly
// access token from cookies and call FastAPI server-to-server — the browser
// never sees a JWT. Every permission check is the backend's; nothing here
// assumes the caller is allowed.

async function run(
  fn: () => Promise<unknown>,
  ...paths: string[]
): Promise<ActionResult> {
  try {
    await fn();
  } catch (err) {
    return toActionError(err);
  }
  for (const p of paths) revalidatePath(p, "layout");
  return { ok: true };
}

/** Like `run`, but hands the backend's response back to the caller. */
async function runWith<T>(
  fn: () => Promise<T>,
  ...paths: string[]
): Promise<ActionResult<T>> {
  let data: T;
  try {
    data = await fn();
  } catch (err) {
    return toActionError(err);
  }
  for (const p of paths) revalidatePath(p, "layout");
  return { ok: true, data } as ActionResult<T>;
}

const json = (method: string, body?: unknown): RequestInit => ({
  method,
  body: body === undefined ? undefined : JSON.stringify(body),
});

// --- Events ---

/** Mirrors `EventCreate` / `EventUpdate`; datetimes are naive ISO strings. */
export type EventInput = {
  title: string;
  description: string | null;
  start_date: string;
  end_date: string;
  registrations_limits: number;
};

export async function registerForEvent(eventId: number) {
  return run(
    () => apiJson(`/event/${eventId}/register`, { method: "POST" }),
    "/"
  );
}

export async function unregisterFromEvent(eventId: number) {
  return run(
    () => apiJson(`/event/${eventId}/register`, { method: "DELETE" }),
    "/"
  );
}

export async function createEvent(body: EventInput) {
  return runWith(() => apiJson<EventOut>("/event/", json("POST", body)), "/");
}

export async function updateEvent(eventId: number, body: Partial<EventInput>) {
  return runWith(
    () => apiJson<EventOut>(`/event/${eventId}`, json("PUT", body)),
    "/"
  );
}

export async function deleteEvent(eventId: number) {
  return run(() => apiJson(`/event/${eventId}`, { method: "DELETE" }), "/");
}

export async function checkInUser(eventId: number, userId: number) {
  return run(
    () => apiJson(`/event/${eventId}/checkin/${userId}`, { method: "POST" }),
    "/"
  );
}

export async function undoCheckIn(eventId: number, userId: number) {
  return run(
    () => apiJson(`/event/${eventId}/checkin/${userId}`, { method: "DELETE" }),
    "/"
  );
}

// --- Profile / account ---

export type ProfileUpdate = {
  username?: string;
  firstname?: string;
  name?: string;
  mail?: string;
  phone?: string;
  birth_date?: string;
  password?: string;
};

export async function updateMe(body: ProfileUpdate) {
  return run(() => apiJson("/user/me", json("PUT", body)), "/");
}

/** Deletes the account (and its Nextcloud one), then drops the now-useless session cookies. */
export async function deleteMe(): Promise<ActionResult> {
  const res = await run(() => apiJson("/user/me", { method: "DELETE" }));
  if (res.ok) {
    const store = await cookies();
    store.delete(ACCESS_COOKIE);
    store.delete(REFRESH_COOKIE);
  }
  return res;
}

// --- Notifications ---

export async function markNotificationRead(id: number) {
  return run(
    () => apiJson(`/user/notification/read/${id}`, { method: "PUT" }),
    "/"
  );
}

export async function markNotificationUnread(id: number) {
  return run(
    () => apiJson(`/user/notification/unread/${id}`, { method: "PUT" }),
    "/"
  );
}

export async function markAllNotificationsRead() {
  return run(
    () => apiJson("/user/notification/read-all", { method: "PUT" }),
    "/"
  );
}

export async function deleteNotification(id: number) {
  return run(
    () => apiJson(`/user/notification/${id}`, { method: "DELETE" }),
    "/"
  );
}

/** Staff/admin: notify one user. */
export async function sendNotification(userId: number, message: string) {
  return run(() =>
    apiJson("/user/notification/", json("POST", { user_id: userId, message }))
  );
}

/** Admin: notify everyone, or only the holders of `role`. Returns how many were sent. */
export async function broadcastNotification(
  message: string,
  role: string | null = null
) {
  return runWith(
    async () =>
      (
        await apiJson<{ sent: number }>(
          "/user/notification/broadcast",
          json("POST", { message, role })
        )
      ).sent,
    "/"
  );
}

// --- Reminders ---

export async function createReminder(body: {
  date: string;
  title: string;
  description: string | null;
}) {
  return run(() => apiJson("/user/reminder/", json("POST", body)), "/");
}

export async function deleteReminder(id: number) {
  return run(() => apiJson(`/user/reminder/${id}`, { method: "DELETE" }), "/");
}

export async function deleteAllReminders() {
  return run(() => apiJson("/user/reminder/", { method: "DELETE" }), "/");
}

// --- Storage (Nextcloud, as the current user) ---

export async function deleteStorageNode(path: string) {
  return run(
    () => apiJson(`/storage/${query({ path })}`, { method: "DELETE" }),
    "/file"
  );
}

export async function setFavourite(path: string, value: boolean) {
  return run(
    () =>
      apiJson(`/storage/favourite${query({ path, value: String(value) })}`, {
        method: "POST",
      }),
    "/file"
  );
}

export async function createFolder(path: string) {
  return run(() => apiJson("/storage/folder", json("POST", { path })), "/file");
}

/** Also used to rename: same folder, new name. Never overwrites. */
export async function moveStorageNode(src: string, dst: string) {
  return run(
    () =>
      apiJson<StorageNode>(
        "/storage/move",
        json("POST", { src, dst, overwrite: false })
      ),
    "/file"
  );
}

export async function copyStorageNode(src: string, dst: string) {
  return run(
    () =>
      apiJson<StorageNode>(
        "/storage/copy",
        json("POST", { src, dst, overwrite: false })
      ),
    "/file"
  );
}

// --- Nextcloud account link (Login Flow v2) ---

export async function startNextcloudLink() {
  return runWith(() =>
    apiJson<NcLinkInit>("/nextcloud/link/init", { method: "POST" })
  );
}

// No revalidation here: it would re-render the page on every poll. The caller
// refreshes once the link is done.
export async function pollNextcloudLink(handle: string) {
  return runWith(() =>
    apiJson<NcLinkPoll>(`/nextcloud/link/poll/${encodeURIComponent(handle)}`)
  );
}

export async function unlinkNextcloud() {
  return run(
    () => apiJson("/nextcloud/link", { method: "DELETE" }),
    "/profile"
  );
}

// --- Admin ---

export async function deleteUser(userId: number) {
  return run(
    () => apiJson(`/user/${userId}`, { method: "DELETE" }),
    "/adminUser"
  );
}

export async function setNextcloudUserEnabled(
  username: string,
  enabled: boolean
) {
  return run(
    () =>
      apiJson(
        `/nextcloud/users/${encodeURIComponent(username)}/${enabled ? "enable" : "disable"}`,
        {
          method: "PUT",
        }
      ),
    "/adminEvent"
  );
}
