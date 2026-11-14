"use client";

import { Check } from "lucide-react";
import { useState, useTransition } from "react";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { checkInUser, undoCheckIn } from "@/lib/actions";
import { initialsOf } from "@/lib/roles";
import type { EventOut, PeopleById } from "@/lib/types";

/** Staff/admin check-in of the registered users (POST/DELETE /event/{id}/checkin/{user_id}). */
export function EventAttendanceSheet({
  open,
  onOpenChange,
  event,
  people,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  event: EventOut;
  people?: PeopleById;
}) {
  const [pending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);

  function toggle(userId: number, present: boolean) {
    setError(null);
    startTransition(async () => {
      const res = present
        ? await undoCheckIn(event.id, userId)
        : await checkInUser(event.id, userId);
      if (!res.ok) setError(res.error);
    });
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="overflow-y-auto">
        <SheetHeader>
          <SheetTitle>Présences</SheetTitle>
          <SheetDescription>
            {event.title} — {event.attendee_ids.length}/{event.registered_count} présents
          </SheetDescription>
        </SheetHeader>
        <div className="flex flex-col gap-2 px-4 pb-4">
          {error && <p className="text-sm text-destructive">{error}</p>}
          {event.registered_user_ids.length === 0 && (
            <p className="text-sm text-muted-foreground">Aucun inscrit.</p>
          )}
          {event.registered_user_ids.map((id) => {
            const person = people?.[id];
            const present = event.attendee_ids.includes(id);
            return (
              <div
                key={id}
                className="flex items-center gap-3 rounded-md border border-border p-3 text-sm"
              >
                <Avatar className="size-8">
                  <AvatarFallback className="bg-primary text-xs font-semibold text-primary-foreground">
                    {person ? initialsOf(person.firstname, person.name) : "#"}
                  </AvatarFallback>
                </Avatar>
                <div className="flex min-w-0 flex-1 flex-col">
                  <span className="truncate font-medium">
                    {person ? `${person.firstname} ${person.name}` : `Adhérent n°${id}`}
                  </span>
                  {person && (
                    <span className="truncate text-xs text-muted-foreground">
                      @{person.username}
                    </span>
                  )}
                </div>
                <Button
                  size="sm"
                  variant={present ? "default" : "outline"}
                  disabled={pending}
                  onClick={() => toggle(id, present)}
                >
                  {present && <Check />}
                  {present ? "Présent" : "Pointer"}
                </Button>
              </div>
            );
          })}
        </div>
      </SheetContent>
    </Sheet>
  );
}
