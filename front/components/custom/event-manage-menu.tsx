"use client";

import { ClipboardCheck, MoreHorizontal, Pencil, Trash2 } from "lucide-react";
import { useState } from "react";

import { EventAttendanceSheet } from "@/components/custom/event-attendance-sheet";
import { EventFormSheet } from "@/components/custom/event-form-sheet";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import type { useEventActions } from "@/hooks/use-event-actions";
import type { EventOut, PeopleById } from "@/lib/types";

/** The "⋯" menu of an event (edit, check-in, delete) and the sheets it opens. */
export function EventManageMenu({
  event,
  people,
  actions,
}: {
  event: EventOut;
  people?: PeopleById;
  actions: ReturnType<typeof useEventActions>;
}) {
  const [sheet, setSheet] = useState<"edit" | "attendance" | null>(null);
  if (!actions.canEdit) return null;

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="ghost"
            size="icon-sm"
            aria-label="Gérer l'évènement"
            disabled={actions.pending}
          >
            <MoreHorizontal className="size-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem onSelect={() => setSheet("edit")}>
            <Pencil className="mr-2 size-4" />
            Modifier
          </DropdownMenuItem>
          {actions.privileged && (
            <DropdownMenuItem onSelect={() => setSheet("attendance")}>
              <ClipboardCheck className="mr-2 size-4" />
              Présences
            </DropdownMenuItem>
          )}
          {actions.canDelete && (
            <>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                className="text-brand-red focus:text-brand-red"
                onSelect={actions.remove}
              >
                <Trash2 className="mr-2 size-4" />
                Supprimer
              </DropdownMenuItem>
            </>
          )}
        </DropdownMenuContent>
      </DropdownMenu>
      <EventFormSheet
        open={sheet === "edit"}
        onOpenChange={(open) => setSheet(open ? "edit" : null)}
        event={event}
      />
      {actions.privileged && (
        <EventAttendanceSheet
          open={sheet === "attendance"}
          onOpenChange={(open) => setSheet(open ? "attendance" : null)}
          event={event}
          people={people}
        />
      )}
    </>
  );
}
