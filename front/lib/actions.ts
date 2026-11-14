"use server";

import { revalidatePath } from "next/cache";

import { type ActionResult, apiJson, query, toActionError } from "@/lib/api";

// Server Actions: they run on the Next.js server, so they read the httpOnly
// access token from cookies and call FastAPI server-to-server — the browser
// never sees a JWT. Every permission check is the backend's; nothing here
// assumes the caller is allowed.

async function run(fn: () => Promise<unknown>, ...paths: string[]): Promise<ActionResult> {
  try {
    await fn();
  } catch (err) {
    return toActionError(err);
  }
  for (const p of paths) revalidatePath(p, "layout");
  return { ok: true };
}

// --- Events ---

export async function registerForEvent(eventId: number) {
  return run(() => apiJson(`/event/${eventId}/register`, { method: "POST" }), "/");
}

export async function unregisterFromEvent(eventId: number) {
  return run(() => apiJson(`/event/${eventId}/register`, { method: "DELETE" }), "/");
}

// --- Profile ---

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
  return run(() => apiJson("/user/me", { method: "PUT", body: JSON.stringify(body) }), "/");
}

// --- Notifications ---

export async function markNotificationRead(id: number) {
  return run(() => apiJson(`/user/notification/read/${id}`, { method: "PUT" }), "/");
}

export async function markAllNotificationsRead() {
  return run(() => apiJson("/user/notification/read-all", { method: "PUT" }), "/");
}

// --- Storage (Nextcloud, as the current user) ---

export async function deleteStorageNode(path: string) {
  return run(() => apiJson(`/storage/${query({ path })}`, { method: "DELETE" }), "/file");
}

export async function setFavourite(path: string, value: boolean) {
  return run(
    () => apiJson(`/storage/favourite${query({ path, value: String(value) })}`, { method: "POST" }),
    "/file",
  );
}

export async function createFolder(path: string) {
  return run(
    () => apiJson("/storage/folder", { method: "POST", body: JSON.stringify({ path }) }),
    "/file",
  );
}

// --- Admin ---

export async function deleteUser(userId: number) {
  return run(() => apiJson(`/user/${userId}`, { method: "DELETE" }), "/adminUser");
}
