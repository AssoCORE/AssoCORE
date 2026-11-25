"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { format, isSameDay, startOfDay } from "date-fns";
import { fr } from "date-fns/locale";
import { BellRing, Plus, Trash2 } from "lucide-react";
import { useMemo, useState, useTransition } from "react";
import { useForm } from "react-hook-form";

import { useAuth } from "@/components/auth/AuthProvider";
import { EventListItem } from "@/components/custom/event-list-item";
import { MiniCalendar } from "@/components/custom/mini-calendar";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Textarea } from "@/components/ui/textarea";
import {
  createReminder,
  deleteAllReminders,
  deleteReminder,
} from "@/lib/actions";
import {
  type ReminderInput,
  reminderSchema,
  toBackendDatetime,
} from "@/lib/schemas";
import type { EventOut, ReminderOut } from "@/lib/types";

export function CalendarView({
  events,
  reminders,
}: {
  events: EventOut[] | null;
  reminders: ReminderOut[] | null;
}) {
  const user = useAuth();
  const [selectedDay, setSelectedDay] = useState<Date | undefined>();
  const [creating, setCreating] = useState(false);
  const [pending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);

  // Reminders win the underline over events on the same day: they are the user's own.
  const markedDays = useMemo(
    () => [
      ...(reminders ?? []).map((r) => ({
        date: new Date(r.date),
        tone: "amber" as const,
      })),
      ...(events ?? []).map((e) => ({
        date: new Date(e.start_date),
        tone: e.registered_user_ids.includes(user.id)
          ? ("green" as const)
          : ("blue" as const),
      })),
    ],
    [events, reminders, user.id]
  );

  // A selected day shows that day; otherwise everything from today on.
  const today = startOfDay(new Date());
  const inView = (d: Date) =>
    selectedDay ? isSameDay(d, selectedDay) : d >= today;
  const visibleReminders = (reminders ?? [])
    .filter((r) => inView(new Date(r.date)))
    .sort((a, b) => a.date.localeCompare(b.date));
  const visibleEvents = (events ?? []).filter((e) =>
    inView(new Date(e.start_date))
  );

  function onDeleteAll() {
    const count = reminders?.length ?? 0;
    if (!window.confirm(`Supprimer vos ${count} rappel(s), passés compris ?`))
      return;
    setError(null);
    startTransition(async () => {
      const res = await deleteAllReminders();
      if (!res.ok) setError(res.error);
    });
  }

  function onDelete(reminder: ReminderOut) {
    if (!window.confirm(`Supprimer le rappel « ${reminder.title} » ?`)) return;
    setError(null);
    startTransition(async () => {
      const res = await deleteReminder(reminder.id);
      if (!res.ok) setError(res.error);
    });
  }

  return (
    <div className="grid flex-1 min-h-0 auto-rows-fr gap-4 md:gap-6 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
      <Card className="h-full min-h-0">
        <CardContent className="flex h-full flex-col p-6">
          <MiniCalendar
            markedDays={markedDays}
            selectedDay={selectedDay}
            onSelectDay={(day) =>
              setSelectedDay(
                selectedDay && isSameDay(day, selectedDay) ? undefined : day
              )
            }
          />
        </CardContent>
      </Card>

      <div className="flex h-full min-h-0 flex-col gap-3">
        <div className="flex items-center justify-between gap-2">
          <h2 className="truncate text-base font-semibold">
            {selectedDay
              ? format(selectedDay, "EEEE d MMMM", { locale: fr })
              : "À venir"}
          </h2>
          <div className="flex shrink-0 gap-2">
            {selectedDay && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSelectedDay(undefined)}
              >
                Tout afficher
              </Button>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCreating(true)}
            >
              <Plus />
              Nouveau rappel
            </Button>
          </div>
        </div>
        {error && <p className="text-sm text-destructive">{error}</p>}

        <div className="flex flex-1 flex-col gap-3 overflow-y-auto pr-1">
          {reminders === null ? (
            <p className="text-sm text-destructive">
              Impossible de charger les rappels.
            </p>
          ) : (
            visibleReminders.map((r) => (
              <div
                key={`r-${r.id}`}
                className="flex items-start justify-between gap-3 rounded-md border border-border bg-card p-4"
              >
                <div className="min-w-0 flex-1">
                  <p className="flex items-center gap-1.5 truncate text-sm font-semibold">
                    <BellRing className="size-3.5 shrink-0 text-role-tresorier" />
                    {r.title}
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {format(new Date(r.date), "d MMM yyyy · HH:mm", {
                      locale: fr,
                    })}
                  </p>
                  {r.description && (
                    <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">
                      {r.description}
                    </p>
                  )}
                </div>
                <Button
                  variant="ghost"
                  size="icon-sm"
                  aria-label="Supprimer le rappel"
                  disabled={pending}
                  onClick={() => onDelete(r)}
                >
                  <Trash2 className="size-4" />
                </Button>
              </div>
            ))
          )}
          {events === null ? (
            <p className="text-sm text-destructive">
              Impossible de charger les événements.
            </p>
          ) : (
            visibleEvents.map((e) => (
              <EventListItem key={`e-${e.id}`} event={e} />
            ))
          )}
          {visibleReminders.length === 0 && visibleEvents.length === 0 && (
            <p className="text-sm text-muted-foreground">Rien de prévu.</p>
          )}
        </div>
        {!!reminders?.length && (
          <Button
            variant="ghost"
            size="sm"
            className="self-end text-brand-red hover:text-brand-red"
            onClick={onDeleteAll}
            disabled={pending}
          >
            <Trash2 />
            Supprimer tous mes rappels
          </Button>
        )}
      </div>

      <ReminderSheet
        open={creating}
        onOpenChange={setCreating}
        day={selectedDay}
      />
    </div>
  );
}

function ReminderSheet({
  open,
  onOpenChange,
  day,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  day?: Date;
}) {
  // SheetContent unmounts when closed, so each opening starts a fresh form.
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="overflow-y-auto">
        <ReminderForm day={day} onDone={() => onOpenChange(false)} />
      </SheetContent>
    </Sheet>
  );
}

function ReminderForm({ day, onDone }: { day?: Date; onDone: () => void }) {
  const [pending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);
  // Pre-filled with the selected day at 09:00 so a reminder lands where the user is looking.
  const form = useForm<ReminderInput>({
    resolver: zodResolver(reminderSchema),
    defaultValues: {
      title: "",
      date: day ? `${format(day, "yyyy-MM-dd")}T09:00` : "",
      description: "",
    },
  });

  function onSubmit(values: ReminderInput) {
    setError(null);
    startTransition(async () => {
      const res = await createReminder({
        title: values.title.trim(),
        date: toBackendDatetime(values.date),
        description: values.description.trim() || null,
      });
      if (res.ok) onDone();
      else setError(res.error);
    });
  }

  return (
    <>
      <SheetHeader>
        <SheetTitle>Nouveau rappel</SheetTitle>
        <SheetDescription>Visible uniquement par vous.</SheetDescription>
      </SheetHeader>
      <Form {...form}>
        <form
          onSubmit={form.handleSubmit(onSubmit)}
          className="flex flex-col gap-4 px-4 pb-4"
        >
          <FormField
            control={form.control}
            name="title"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="text-xs font-medium text-muted-foreground">
                  Titre
                </FormLabel>
                <FormControl>
                  <Input {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="date"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="text-xs font-medium text-muted-foreground">
                  Date
                </FormLabel>
                <FormControl>
                  <Input type="datetime-local" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="description"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="text-xs font-medium text-muted-foreground">
                  Description
                </FormLabel>
                <FormControl>
                  <Textarea rows={3} {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          {error && <p className="text-sm text-destructive">{error}</p>}
          <Button type="submit" disabled={pending}>
            {pending ? "Enregistrement…" : "Créer le rappel"}
          </Button>
        </form>
      </Form>
    </>
  );
}
