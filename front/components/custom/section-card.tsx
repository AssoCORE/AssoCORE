import type { ReactNode } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export function SectionCard({
  title,
  icon,
  children,
  footer,
  className,
  contentClassName,
}: {
  title: ReactNode;
  icon?: ReactNode;
  children: ReactNode;
  footer?: ReactNode;
  className?: string;
  contentClassName?: string;
}) {
  return (
    <Card className={cn("flex flex-col gap-4", className)}>
      <CardHeader className="pb-0">
        <CardTitle className="flex items-center gap-2 text-base font-semibold">
          {icon}
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent
        className={cn(
          "flex flex-1 flex-col gap-3 overflow-y-auto",
          contentClassName,
        )}
      >
        {children}
      </CardContent>
      {footer && <div className="border-t border-border p-3">{footer}</div>}
    </Card>
  );
}
