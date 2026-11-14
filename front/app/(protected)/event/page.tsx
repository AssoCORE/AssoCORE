import { EventsView } from "@/app/(protected)/event/events-view";
import { apiJson, query } from "@/lib/api";
import type { EventOut, Page } from "@/lib/types";

export default async function EventPage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string }>;
}) {
  const { q } = await searchParams;
  // 200 is the backend's MAX_PAGE_SIZE; the calendar needs every event, not a page.
  const events = await apiJson<Page<EventOut>>(`/event/${query({ q, limit: 200 })}`).catch(
    () => null,
  );

  return <EventsView events={events?.items ?? null} total={events?.total ?? 0} />;
}
