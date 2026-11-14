"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useState, useTransition } from "react";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
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
import { createEvent, type EventInput, updateEvent } from "@/lib/actions";
import { type EventFormInput, eventSchema, toBackendDatetime, toLocalInput } from "@/lib/schemas";
import type { EventOut } from "@/lib/types";

function defaultsOf(event?: EventOut): EventFormInput {
  return {
    title: event?.title ?? "",
    description: event?.description ?? "",
    start_date: event ? toLocalInput(event.start_date) : "",
    end_date: event ? toLocalInput(event.end_date) : "",
    registrations_limits: event ? String(event.registrations_limits) : "",
  };
}

/** Create an event (no `event`) or edit one. Staff/admin, or the creator, server-side. */
export function EventFormSheet({
  open,
  onOpenChange,
  event,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  event?: EventOut;
}) {
  // SheetContent unmounts when closed, so the form below starts fresh — from the
  // event as it is now — every time the sheet opens.
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="overflow-y-auto">
        <EventForm event={event} onDone={() => onOpenChange(false)} />
      </SheetContent>
    </Sheet>
  );
}

function EventForm({ event, onDone }: { event?: EventOut; onDone: () => void }) {
  const [pending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);
  const form = useForm<EventFormInput>({
    resolver: zodResolver(eventSchema),
    defaultValues: defaultsOf(event),
  });

  function onSubmit(values: EventFormInput) {
    const body: EventInput = {
      title: values.title.trim(),
      description: values.description.trim() || null,
      start_date: toBackendDatetime(values.start_date),
      end_date: toBackendDatetime(values.end_date),
      registrations_limits: Number(values.registrations_limits),
    };
    setError(null);
    startTransition(async () => {
      const res = event ? await updateEvent(event.id, body) : await createEvent(body);
      if (res.ok) onDone();
      else setError(res.error);
    });
  }

  return (
    <>
      <SheetHeader>
        <SheetTitle>{event ? "Modifier l'évènement" : "Nouvel évènement"}</SheetTitle>
        <SheetDescription>
          {event
            ? "Les inscrits seront notifiés de la modification."
            : "L'évènement sera visible par tous les adhérents."}
        </SheetDescription>
      </SheetHeader>
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="flex flex-col gap-4 px-4 pb-4">
          <FormField
            control={form.control}
            name="title"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="text-xs font-medium text-muted-foreground">Titre</FormLabel>
                <FormControl>
                  <Input {...field} />
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
                  <Textarea rows={4} {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="start_date"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="text-xs font-medium text-muted-foreground">Début</FormLabel>
                <FormControl>
                  <Input type="datetime-local" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="end_date"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="text-xs font-medium text-muted-foreground">Fin</FormLabel>
                <FormControl>
                  <Input type="datetime-local" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="registrations_limits"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="text-xs font-medium text-muted-foreground">
                  Nombre de places
                </FormLabel>
                <FormControl>
                  <Input type="number" min={1} step={1} inputMode="numeric" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          {error && <p className="text-sm text-destructive">{error}</p>}
          <Button type="submit" disabled={pending}>
            {pending ? "Enregistrement…" : event ? "Enregistrer" : "Créer l'évènement"}
          </Button>
        </form>
      </Form>
    </>
  );
}
