"use client";

import { Calendar, Users } from "lucide-react";
import { useState, useTransition } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { registerForEvent, unregisterFromEvent } from "@/lib/actions";
import { formatEventRange } from "@/lib/format";
import type { EventOut } from "@/lib/types";
import { cn } from "@/lib/utils";

export function EventCard({ event }: { event: EventOut }) {
  const user = useAuth();
  const [pending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);

  const registered = event.registered_user_ids.includes(user.id);
  const past = new Date(event.end_date) < new Date();
  const status = registered
    ? { label: "Inscrit", className: "bg-emerald-100 text-emerald-800 hover:bg-emerald-100" }
    : event.is_full
      ? { label: "Complet", className: "bg-red-100 text-red-800 hover:bg-red-100" }
      : {
          label: `${event.spots_left} place${event.spots_left > 1 ? "s" : ""}`,
          className: "bg-sky-100 text-sky-800 hover:bg-sky-100",
        };

  function toggle() {
    setError(null);
    startTransition(async () => {
      const res = registered
        ? await unregisterFromEvent(event.id)
        : await registerForEvent(event.id);
      if (!res.ok) setError(res.error);
    });
  }

  return (
    <Card>
      <CardContent className="flex gap-4 p-4">
        <div
          className={cn(
            "relative hidden size-24 shrink-0 rounded-md sm:block",
            registered
              ? "bg-gradient-to-br from-emerald-200 to-emerald-400"
              : "bg-gradient-to-br from-sky-200 to-sky-400",
          )}
          aria-hidden
        />
        <div className="flex min-w-0 flex-1 flex-col gap-2">
          <div className="flex items-start justify-between gap-2">
            <h3 className="truncate text-base font-semibold">{event.title}</h3>
            <Badge className={cn("shrink-0 whitespace-nowrap", status.className)}>
              {status.label}
            </Badge>
          </div>
          {event.description && (
            <p className="line-clamp-2 text-sm text-muted-foreground">{event.description}</p>
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
          {!past && (
            <div className="mt-1 flex gap-2">
              <Button
                size="sm"
                variant={registered ? "outline" : "default"}
                className="flex-1"
                disabled={pending || (!registered && event.is_full)}
                onClick={toggle}
              >
                {registered ? "Se désinscrire" : event.is_full ? "Complet" : "S'inscrire"}
              </Button>
            </div>
          )}
          {error && <p className="text-xs text-destructive">{error}</p>}
        </div>
      </CardContent>
    </Card>
  );
}
