import { Calendar, MapPin, Users, Wallet } from "lucide-react";
import { format } from "date-fns";
import { fr } from "date-fns/locale";

import type { Event, EventCategory } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

const toneBadge: Record<EventCategory["tone"], string> = {
  amber: "bg-amber-100 text-amber-800 hover:bg-amber-100",
  purple: "bg-violet-100 text-violet-800 hover:bg-violet-100",
  red: "bg-red-100 text-red-800 hover:bg-red-100",
  blue: "bg-sky-100 text-sky-800 hover:bg-sky-100",
  green: "bg-emerald-100 text-emerald-800 hover:bg-emerald-100",
};

const toneBg: Record<EventCategory["tone"], string> = {
  amber: "bg-gradient-to-br from-amber-200 to-amber-400",
  purple: "bg-gradient-to-br from-violet-200 to-violet-400",
  red: "bg-gradient-to-br from-red-200 to-red-400",
  blue: "bg-gradient-to-br from-sky-200 to-sky-400",
  green: "bg-gradient-to-br from-emerald-200 to-emerald-400",
};

export function EventCard({ event }: { event: Event }) {
  const day = format(event.startsAt, "d MMMM yyyy", { locale: fr });
  const start = format(event.startsAt, "HH:mm");
  const end = format(event.endsAt, "HH:mm");
  const price = event.price === "Gratuit" ? "Gratuit" : `${event.price} €`;

  return (
    <Card>
      <CardContent className="flex gap-4 p-4">
        <div
          className={cn(
            "relative hidden size-24 shrink-0 rounded-md sm:block",
            toneBg[event.category.tone],
          )}
          aria-hidden
        />
        <div className="flex min-w-0 flex-1 flex-col gap-2">
          <div className="flex items-start justify-between gap-2">
            <h3 className="truncate text-base font-semibold">{event.title}</h3>
            <Badge className={cn("shrink-0 whitespace-nowrap", toneBadge[event.category.tone])}>
              {event.category.label}
            </Badge>
          </div>
          <p className="line-clamp-2 text-sm text-muted-foreground">
            {event.description}
          </p>
          <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-xs text-muted-foreground">
            <span className="flex items-center gap-1.5">
              <Calendar className="size-3.5" />
              {day} · {start} à {end}
            </span>
            <span className="flex items-center gap-1.5">
              <MapPin className="size-3.5" />
              {event.location}
            </span>
            <span className="flex items-center gap-1.5">
              <Users className="size-3.5" />
              {event.participants.current}/{event.participants.max} participants
            </span>
            <span className="flex items-center gap-1.5">
              <Wallet className="size-3.5" />
              {price}
            </span>
          </div>
          <div className="mt-1 flex gap-2">
            <Button variant="outline" size="sm" className="flex-1">
              Voir Plus
            </Button>
            <Button size="sm" className="flex-1">
              S&apos;inscrire
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
