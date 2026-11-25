import { CalendarView } from "@/components/custom/calendar-view";
import { apiJson } from "@/lib/api";
import type { EventOut, Page, ReminderOut } from "@/lib/types";

// The user's agenda: every event plus their own reminders. 200 is the backend's
// MAX_PAGE_SIZE, the calendar needs the whole set rather than a page.
export default async function CalendarPage() {
  const [events, reminders] = await Promise.all([
    apiJson<Page<EventOut>>("/event/?limit=200").catch(() => null),
    apiJson<Page<ReminderOut>>("/user/reminder/?limit=200").catch(() => null),
  ]);

  return (
    <CalendarView
      events={events?.items ?? null}
      reminders={reminders?.items ?? null}
    />
  );
}
