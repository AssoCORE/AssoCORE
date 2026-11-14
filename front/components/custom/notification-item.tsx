import { format } from "date-fns";
import { fr } from "date-fns/locale";

import type { NotificationOut } from "@/lib/types";
import { cn } from "@/lib/utils";

export function NotificationItem({ notification }: { notification: NotificationOut }) {
  return (
    <div className="flex items-start justify-between gap-3 rounded-md border border-border p-4 text-sm">
      <span className={cn(!notification.read && "font-semibold")}>{notification.message}</span>
      <span className="shrink-0 text-xs text-muted-foreground tabular-nums">
        {format(new Date(notification.date), "d MMM · HH:mm", { locale: fr })}
      </span>
    </div>
  );
}
