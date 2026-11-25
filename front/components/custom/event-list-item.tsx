import { Badge } from "@/components/ui/badge";
import { formatEventRange } from "@/lib/format";
import type { EventOut } from "@/lib/types";

export function EventListItem({ event }: { event: EventOut }) {
  return (
    <div className="flex items-start justify-between gap-3 rounded-md border border-border p-4">
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-semibold">{event.title} :</p>
        <p className="mt-1 text-xs text-muted-foreground">
          {formatEventRange(event, "d MMM yyyy")}
        </p>
      </div>
      <Badge className="bg-primary/90 text-primary-foreground hover:bg-primary">
        {event.registered_count}/{event.registrations_limits}
      </Badge>
    </div>
  );
}
