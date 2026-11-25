"use client";

import { Calendar, Users } from "lucide-react";
import Link from "next/link";

import { EventManageMenu } from "@/components/custom/event-manage-menu";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { eventStatus, useEventActions } from "@/hooks/use-event-actions";
import { formatEventRange } from "@/lib/format";
import type { EventOut, PeopleById } from "@/lib/types";
import { cn } from "@/lib/utils";

export function EventCard({
  event,
  people,
}: {
  event: EventOut;
  people?: PeopleById;
}) {
  const actions = useEventActions(event);
  const { registered, past, pending, error } = actions;
  const status = eventStatus(event, registered);

  return (
    <Card>
      <CardContent className="flex gap-4 p-4">
        <div
          className={cn(
            "relative hidden size-24 shrink-0 rounded-md sm:block",
            registered
              ? "bg-gradient-to-br from-emerald-200 to-emerald-400"
              : "bg-gradient-to-br from-sky-200 to-sky-400"
          )}
          aria-hidden
        />
        <div className="flex min-w-0 flex-1 flex-col gap-2">
          <div className="flex items-start justify-between gap-2">
            <h3 className="truncate text-base font-semibold">{event.title}</h3>
            <div className="flex shrink-0 items-center gap-1">
              <Badge
                className={cn("shrink-0 whitespace-nowrap", status.className)}
              >
                {status.label}
              </Badge>
              <EventManageMenu
                event={event}
                people={people}
                actions={actions}
              />
            </div>
          </div>
          {event.description && (
            <p className="line-clamp-2 text-sm text-muted-foreground">
              {event.description}
            </p>
          )}
          <div className="grid gap-x-3 gap-y-1 text-xs text-muted-foreground sm:grid-cols-2">
            <span className="flex items-center gap-1.5">
              <Calendar className="size-3.5" />
              {formatEventRange(event)}
            </span>
            <span className="flex items-center gap-1.5">
              <Users className="size-3.5" />
              {event.registered_count}/{event.registrations_limits} participants
            </span>
          </div>
          <div className="mt-1 flex gap-2">
            <Button asChild size="sm" variant="secondary" className="flex-1">
              <Link href={`/event/${event.id}`}>Voir plus</Link>
            </Button>
            {!past && (
              <Button
                size="sm"
                variant={registered ? "outline" : "default"}
                className="flex-1"
                disabled={pending || (!registered && event.is_full)}
                onClick={actions.toggleRegistration}
              >
                {registered
                  ? "Se désinscrire"
                  : event.is_full
                    ? "Complet"
                    : "S'inscrire"}
              </Button>
            )}
          </div>
          {error && <p className="text-xs text-destructive">{error}</p>}
        </div>
      </CardContent>
    </Card>
  );
}
