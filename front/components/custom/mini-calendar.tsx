"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";
import {
  addMonths,
  eachDayOfInterval,
  endOfMonth,
  endOfWeek,
  format,
  isSameDay,
  isSameMonth,
  startOfMonth,
  startOfWeek,
  subMonths,
} from "date-fns";
import { fr } from "date-fns/locale";
import { useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type MarkedDay = {
  date: Date;
  tone: "green" | "purple" | "red" | "amber" | "blue";
};

const toneClass: Record<MarkedDay["tone"], string> = {
  green: "decoration-primary",
  purple: "decoration-role-president",
  red: "decoration-brand-red",
  amber: "decoration-role-tresorier",
  blue: "decoration-role-user",
};

export function MiniCalendar({
  initialMonth = new Date(),
  markedDays = [],
  onSelectDay,
  selectedDay,
}: {
  initialMonth?: Date;
  markedDays?: MarkedDay[];
  onSelectDay?: (day: Date) => void;
  selectedDay?: Date;
}) {
  const [month, setMonth] = useState<Date>(startOfMonth(initialMonth));

  const days = useMemo(() => {
    const start = startOfWeek(startOfMonth(month), { weekStartsOn: 1 });
    const end = endOfWeek(endOfMonth(month), { weekStartsOn: 1 });
    return eachDayOfInterval({ start, end });
  }, [month]);

  const weekDays = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"];

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="text-primary hover:bg-primary/10"
          onClick={() => setMonth(subMonths(month, 1))}
          aria-label="Mois précédent"
        >
          <ChevronLeft className="size-6" />
        </Button>
        <h2 className="text-2xl font-bold uppercase tracking-wide text-primary">
          {format(month, "MMMM", { locale: fr })}
        </h2>
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="text-primary hover:bg-primary/10"
          onClick={() => setMonth(addMonths(month, 1))}
          aria-label="Mois suivant"
        >
          <ChevronRight className="size-6" />
        </Button>
      </div>

      <div className="grid grid-cols-7 border-b border-border pb-2 text-center text-sm font-medium text-muted-foreground">
        {weekDays.map((wd) => (
          <span key={wd}>{wd}</span>
        ))}
      </div>

      <div className="grid grid-cols-7 gap-y-3">
        {days.map((day) => {
          const inMonth = isSameMonth(day, month);
          const marked = markedDays.find((m) => isSameDay(m.date, day));
          const selected = selectedDay && isSameDay(day, selectedDay);
          return (
            <button
              type="button"
              key={day.toISOString()}
              onClick={() => onSelectDay?.(day)}
              className={cn(
                "mx-auto flex size-9 items-center justify-center rounded-md text-sm tabular-nums transition",
                inMonth ? "text-foreground" : "text-muted-foreground/50",
                selected && "bg-primary/10 font-semibold text-primary",
                marked && "underline decoration-2 underline-offset-4",
                marked && toneClass[marked.tone],
                "hover:bg-primary/5",
              )}
            >
              {format(day, "dd")}
            </button>
          );
        })}
      </div>
    </div>
  );
}
