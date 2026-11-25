import { notFound } from "next/navigation";

import { EventDetail } from "@/components/custom/event-detail";
import { apiJson } from "@/lib/api";
import { peopleById } from "@/lib/auth/admin";
import { isAdmin } from "@/lib/auth/roles";
import { getCurrentUser } from "@/lib/auth/session";
import { BackendError } from "@/lib/backend";
import type { EventOut } from "@/lib/types";

export default async function EventDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  if (!/^\d+$/.test(id)) notFound();

  let event: EventOut;
  try {
    event = await apiJson<EventOut>(`/event/${id}`);
  } catch (err) {
    if (err instanceof BackendError && err.status === 404) notFound();
    throw err;
  }

  const user = await getCurrentUser();
  const people = user && isAdmin(user) ? await peopleById() : undefined;

  return <EventDetail event={event} people={people} />;
}
