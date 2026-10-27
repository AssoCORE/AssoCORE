import type { ReactNode } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

type Props = {
  label: string;
  value: ReactNode;
  hint?: ReactNode;
  accent?: "default" | "primary" | "danger";
  className?: string;
};

const accentClass: Record<NonNullable<Props["accent"]>, string> = {
  default: "text-foreground",
  primary: "text-primary",
  danger: "text-brand-red",
};

export function StatCard({ label, value, hint, accent = "default", className }: Props) {
  return (
    <Card className={cn("bg-card", className)}>
      <CardContent className="flex flex-col gap-1 p-5">
        <span className="text-sm font-medium text-muted-foreground">{label}</span>
        <span className={cn("text-3xl font-semibold leading-tight", accentClass[accent])}>
          {value}
        </span>
        {hint && <span className="text-xs text-muted-foreground">{hint}</span>}
      </CardContent>
    </Card>
  );
}
