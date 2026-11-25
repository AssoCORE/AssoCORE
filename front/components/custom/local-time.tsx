"use client";

import { format } from "date-fns";
import { fr } from "date-fns/locale";
import { useSyncExternalStore } from "react";

import { parseServerDate } from "@/lib/format";
import { cn } from "@/lib/utils";

const noop = () => () => {};

/**
 * A backend-generated (UTC) timestamp shown in the viewer's own timezone. The
 * server only knows its own timezone (UTC in the container), so the text is
 * formatted in the browser, after hydration. Until then an invisible copy of
 * the UTC time holds the space, so the layout does not shift.
 */
export function LocalTime({
  iso,
  pattern,
  className,
}: {
  iso: string;
  pattern: string;
  className?: string;
}) {
  // false during SSR and hydration, true afterwards — without a setState-in-effect.
  const inBrowser = useSyncExternalStore(
    noop,
    () => true,
    () => false
  );
  const date = parseServerDate(iso);
  return (
    <time
      dateTime={date.toISOString()}
      className={cn(className, !inBrowser && "invisible")}
    >
      {format(
        inBrowser
          ? date
          : new Date(date.getTime() + date.getTimezoneOffset() * 60_000),
        pattern,
        {
          locale: fr,
        }
      )}
    </time>
  );
}
