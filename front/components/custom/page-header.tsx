import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export function PageHeader({
  title,
  actions,
  className,
}: {
  title: ReactNode;
  actions?: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-col gap-2 rounded-lg bg-card p-6 shadow-sm md:flex-row md:items-center md:justify-between",
        className,
      )}
    >
      <h1 className="text-center text-lg font-semibold md:text-left md:text-xl">
        {title}
      </h1>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  );
}
