import type { Event } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { format } from "date-fns";
import { fr } from "date-fns/locale";

export function EventListItem({ event }: { event: Event }) {
  const day = format(event.startsAt, "d MMM yyyy", { locale: fr });
  const start = format(event.startsAt, "HH:mm");
  const end = format(event.endsAt, "HH:mm");
  return (
    <div className="flex items-start justify-between gap-3 rounded-md border border-border p-4">
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-semibold">{event.title} :</p>
        <p className="mt-1 text-xs text-muted-foreground">
          {day} · {start} à {end}
        </p>
      </div>
      <Badge className="bg-primary/90 text-primary-foreground hover:bg-primary">
        {event.participants.current}/{event.participants.max}
      </Badge>
    </div>
  );
}
