import { notFound } from "next/navigation";

import { UserDetail } from "@/components/custom/user-detail";
import { apiJson } from "@/lib/api";
import { BackendError } from "@/lib/backend";
import type { UserOut } from "@/lib/types";

// Admin-only: the (admin) layout redirects others, and GET /user/{id} is
// require_admin on the backend regardless.
export default async function AdminUserDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  if (!/^\d+$/.test(id)) notFound();

  let user: UserOut;
  try {
    user = await apiJson<UserOut>(`/user/${id}`);
  } catch (err) {
    if (err instanceof BackendError && err.status === 404) notFound();
    throw err;
  }

  // Only the fields the page shows cross to the client: UserOut also carries the
  // user's notifications and reminders, which stay private.
  const { notifications, reminders, ...profile } = user;
  return (
    <UserDetail
      user={profile}
      unread={notifications.filter((n) => !n.read).length}
      reminders={reminders.length}
    />
  );
}
