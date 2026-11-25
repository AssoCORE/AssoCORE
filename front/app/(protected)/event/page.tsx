import { type EventFilter, EventsView } from "@/components/custom/events-view";
import { apiJson, query } from "@/lib/api";
import { peopleById } from "@/lib/auth/admin";
import { isAdmin } from "@/lib/auth/roles";
import { getCurrentUser } from "@/lib/auth/session";
import type { EventOut, Page } from "@/lib/types";

const filters: Record<EventFilter, Record<string, boolean>> = {
  all: {},
  upcoming: { upcoming: true },
  past: { past: true },
  mine: { my_events: true },
};

export default async function EventPage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string; filter?: string }>;
}) {
  const { q, filter: raw } = await searchParams;
  const filter: EventFilter =
    raw && raw in filters ? (raw as EventFilter) : "all";
  const user = await getCurrentUser();

  // 200 is the backend's MAX_PAGE_SIZE; the calendar needs every event, not a page.
  // Only admins may list users (GET /user/), so only they get names on the check-in sheet.
  const [events, people] = await Promise.all([
    apiJson<Page<EventOut>>(
      `/event/${query({ q, ...filters[filter], limit: 200 })}`
    ).catch(() => null),
    user && isAdmin(user) ? peopleById() : undefined,
  ]);

  return (
    <EventsView
      events={events?.items ?? null}
      total={events?.total ?? 0}
      filter={filter}
      people={people}
    />
  );
}
