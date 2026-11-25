import { LocalTime } from "@/components/custom/local-time";
import type { NotificationOut } from "@/lib/types";
import { cn } from "@/lib/utils";

export function NotificationItem({
  notification,
}: {
  notification: NotificationOut;
}) {
  return (
    <div className="flex items-start justify-between gap-3 rounded-md border border-border p-4 text-sm">
      <span className={cn(!notification.read && "font-semibold")}>
        {notification.message}
      </span>
      <LocalTime
        iso={notification.date}
        pattern="d MMM · HH:mm"
        className="shrink-0 text-xs text-muted-foreground tabular-nums"
      />
    </div>
  );
}
