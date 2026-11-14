"use client";

import { isSameDay } from "date-fns";
import { useMemo, useState } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { EventCard } from "@/components/custom/event-card";
import { MiniCalendar } from "@/components/custom/mini-calendar";
import { SearchBar } from "@/components/custom/search-bar";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useUrlSearch } from "@/hooks/use-url-search";
import type { EventOut } from "@/lib/types";

export function EventsView({ events, total }: { events: EventOut[] | null; total: number }) {
  const user = useAuth();
  const search = useUrlSearch();
  const [selectedDay, setSelectedDay] = useState<Date | undefined>();

  const markedDays = useMemo(
    () =>
      (events ?? []).map((e) => ({
        date: new Date(e.start_date),
        tone: e.registered_user_ids.includes(user.id) ? ("green" as const) : ("blue" as const),
      })),
    [events, user.id],
  );

  const visible = useMemo(() => {
    if (!events) return [];
    if (!selectedDay) return events;
    return events.filter((e) => isSameDay(new Date(e.start_date), selectedDay));
  }, [events, selectedDay]);

  return (
    <div className="grid flex-1 min-h-0 auto-rows-fr gap-4 md:gap-6 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
      <Card className="h-full min-h-0">
        <CardContent className="flex h-full flex-col p-6">
          <MiniCalendar
            markedDays={markedDays}
            selectedDay={selectedDay}
            onSelectDay={(day) =>
              setSelectedDay(selectedDay && isSameDay(day, selectedDay) ? undefined : day)
            }
          />
        </CardContent>
      </Card>

      <div className="flex h-full min-h-0 flex-col gap-3">
        <SearchBar value={search.value} onChange={search.setValue} />
        {selectedDay && (
          <Button
            variant="ghost"
            size="sm"
            className="self-start"
            onClick={() => setSelectedDay(undefined)}
          >
            Afficher tous les jours
          </Button>
        )}
        <div className="flex flex-1 flex-col gap-3 overflow-y-auto pr-1">
          {events === null ? (
            <p className="text-sm text-destructive">Impossible de charger les événements.</p>
          ) : (
            <>
              {visible.map((event) => (
                <EventCard key={event.id} event={event} />
              ))}
              {visible.length === 0 && (
                <p className="text-sm text-muted-foreground">Aucun événement.</p>
              )}
              {total > events.length && (
                <p className="text-xs text-muted-foreground">
                  {events.length} affichés sur {total} — affinez la recherche.
                </p>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
