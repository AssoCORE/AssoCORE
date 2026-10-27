"use client";

import { useMemo, useState } from "react";

import { EventCard } from "@/components/custom/event-card";
import { MiniCalendar } from "@/components/custom/mini-calendar";
import { SearchBar } from "@/components/custom/search-bar";
import { Card, CardContent } from "@/components/ui/card";
import { events } from "@/lib/mock/events";

export default function EventPage() {
  const [query, setQuery] = useState("");
  const [selectedDay, setSelectedDay] = useState<Date | undefined>();

  const markedDays = useMemo(
    () =>
      events.map((e) => ({
        date: e.startsAt,
        tone: e.category.tone,
      })),
    [],
  );

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return events;
    return events.filter((e) =>
      [e.title, e.description, e.location, e.category.label]
        .join(" ")
        .toLowerCase()
        .includes(q),
    );
  }, [query]);

  return (
    <div className="grid flex-1 min-h-0 auto-rows-fr gap-4 md:gap-6 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
      <Card className="h-full min-h-0">
        <CardContent className="flex h-full flex-col p-6">
          <MiniCalendar
            initialMonth={new Date(2026, 6, 1)}
            markedDays={markedDays}
            selectedDay={selectedDay}
            onSelectDay={setSelectedDay}
          />
        </CardContent>
      </Card>

      <div className="flex h-full min-h-0 flex-col gap-3">
        <SearchBar value={query} onChange={setQuery} />
        <div className="flex flex-1 flex-col gap-3 overflow-y-auto pr-1">
          {filtered.map((event) => (
            <EventCard key={event.id} event={event} />
          ))}
          {filtered.length === 0 && (
            <p className="text-sm text-muted-foreground">Aucun événement.</p>
          )}
        </div>
      </div>
    </div>
  );
}
