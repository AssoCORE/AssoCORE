"use client";

import {
  Calendar,
  ChevronLeft,
  ClipboardCheck,
  Ticket,
  Users,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { EventManageMenu } from "@/components/custom/event-manage-menu";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { eventStatus, useEventActions } from "@/hooks/use-event-actions";
import { formatEventRange } from "@/lib/format";
import { initialsOf } from "@/lib/roles";
import type { EventOut, PeopleById } from "@/lib/types";
import { cn } from "@/lib/utils";

export function EventDetail({
  event,
  people,
}: {
  event: EventOut;
  people?: PeopleById;
}) {
  const router = useRouter();
  const actions = useEventActions(event, {
    onDeleted: () => router.push("/event"),
  });
  const { registered, past, pending, error, privileged } = actions;
  const status = eventStatus(event, registered);

  return (
    <div className="flex flex-1 flex-col gap-4 md:gap-6">
      <Button asChild variant="ghost" size="sm" className="self-start">
        <Link href="/event">
          <ChevronLeft />
          Tous les évènements
        </Link>
      </Button>

      <Card className="overflow-hidden p-0">
        <div
          className={cn(
            "h-32 w-full",
            registered
              ? "bg-gradient-to-r from-emerald-200 to-emerald-400"
              : "bg-gradient-to-r from-sky-200 to-sky-400"
          )}
          aria-hidden
        />
      </Card>

      <div className="grid flex-1 min-h-0 grid-cols-[minmax(0,1fr)] gap-4 md:gap-6 lg:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)]">
        <Card className="h-full">
          <CardContent className="flex h-full flex-col gap-5 p-6">
            <header className="flex items-start justify-between gap-3">
              <h1 className="text-xl font-semibold">{event.title}</h1>
              <div className="flex shrink-0 items-center gap-1">
                <Badge className={cn("whitespace-nowrap", status.className)}>
                  {status.label}
                </Badge>
                <EventManageMenu
                  event={event}
                  people={people}
                  actions={actions}
                />
              </div>
            </header>

            <div className="grid gap-3 text-sm sm:grid-cols-2">
              <Info icon={Calendar} label="Date">
                {formatEventRange(event)}
              </Info>
              <Info icon={Users} label="Participants">
                {event.registered_count}/{event.registrations_limits}
              </Info>
              <Info icon={Ticket} label="Places restantes">
                {event.is_full ? "Complet" : event.spots_left}
              </Info>
              {privileged && (
                <Info icon={ClipboardCheck} label="Présents">
                  {event.attendee_ids.length}/{event.registered_count}
                </Info>
              )}
            </div>

            <section className="flex flex-col gap-1 border-t border-border pt-4">
              <h2 className="text-sm font-semibold">Description</h2>
              <p className="whitespace-pre-line text-sm text-muted-foreground">
                {event.description || "Aucune description."}
              </p>
            </section>

            {!past && (
              <Button
                variant={registered ? "outline" : "default"}
                className="self-start"
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
            {past && (
              <p className="text-sm text-muted-foreground">
                Cet évènement est terminé.
              </p>
            )}
            {error && <p className="text-sm text-destructive">{error}</p>}
          </CardContent>
        </Card>

        {privileged && (
          <Card className="h-full">
            <CardContent className="flex h-full flex-col gap-3 overflow-y-auto p-6">
              <h2 className="text-lg font-semibold">Inscrits :</h2>
              {event.registered_user_ids.length === 0 && (
                <p className="text-sm text-muted-foreground">Aucun inscrit.</p>
              )}
              {event.registered_user_ids.map((id) => {
                const person = people?.[id];
                const present = event.attendee_ids.includes(id);
                return (
                  <div key={id} className="flex items-center gap-3 text-sm">
                    <Avatar className="size-8">
                      <AvatarFallback className="bg-primary text-xs font-semibold text-primary-foreground">
                        {person
                          ? initialsOf(person.firstname, person.name)
                          : "#"}
                      </AvatarFallback>
                    </Avatar>
                    <span className="flex-1 truncate">
                      {person
                        ? `${person.firstname} ${person.name}`
                        : `Adhérent n°${id}`}
                    </span>
                    {present && (
                      <Badge className="bg-emerald-100 text-emerald-800 hover:bg-emerald-100">
                        Présent
                      </Badge>
                    )}
                  </div>
                );
              })}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

function Info({
  icon: Icon,
  label,
  children,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-start gap-2">
      <Icon className="mt-0.5 size-4 shrink-0 text-primary" />
      <div className="flex flex-col">
        <span className="text-xs text-muted-foreground">{label}</span>
        <span className="font-medium">{children}</span>
      </div>
    </div>
  );
}
