import type { Activity } from "@/lib/types";

export function ActivityItem({ activity }: { activity: Activity }) {
  return (
    <div className="rounded-md border border-border p-4 text-sm">
      <span className="font-semibold">{activity.actor}</span>{" "}
      <span className="text-muted-foreground">{activity.verb}</span>{" "}
      <span className="text-muted-foreground">{activity.targetKind}</span>{" "}
      <span className="font-semibold">{activity.target}</span>
    </div>
  );
}
