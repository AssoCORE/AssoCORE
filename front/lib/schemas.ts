import { z } from "zod";

// Mirrors the event/reminder schemas in back/app/schemas/classes.py, so client-side
// errors match the backend's 422s. Dates come from <input type="datetime-local">
// ("YYYY-MM-DDTHH:mm") and are sent as the backend's naive ISO datetimes.

const datetimeLocal = z.string().min(1, "Requis");

// EventCreate: title 1-255, registrations_limits > 0, end_date after start_date.
export const eventSchema = z
  .object({
    title: z
      .string()
      .trim()
      .min(1, "Requis")
      .max(255, "255 caractères maximum"),
    description: z.string(),
    start_date: datetimeLocal,
    end_date: datetimeLocal,
    // Kept as the input's string; converted with Number() when sent.
    registrations_limits: z
      .string()
      .regex(/^\d+$/, "Nombre entier attendu")
      .refine((v) => Number(v) > 0, "Doit être supérieur à 0"),
  })
  .refine((v) => v.end_date > v.start_date, {
    path: ["end_date"],
    message: "La fin doit être après le début",
  });
export type EventFormInput = z.infer<typeof eventSchema>;

// ReminderCreate: date + title required, description optional.
export const reminderSchema = z.object({
  title: z.string().trim().min(1, "Requis"),
  date: datetimeLocal,
  description: z.string(),
});
export type ReminderInput = z.infer<typeof reminderSchema>;

// NotificationCreate / NotificationBroadcast: message 1-2000 characters.
export const NOTIFICATION_MAX_LENGTH = 2000;

/** Error message for a notification text, or null when the backend will accept it. */
export function notificationMessageError(message: string): string | null {
  if (!message) return "Le message est vide.";
  if (message.length > NOTIFICATION_MAX_LENGTH) {
    return `Le message dépasse ${NOTIFICATION_MAX_LENGTH} caractères.`;
  }
  return null;
}

/** `<input type="datetime-local">` value → naive ISO datetime the backend expects. */
export const toBackendDatetime = (local: string) =>
  local.length === 16 ? `${local}:00` : local;

/** Naive ISO datetime from the backend → `<input type="datetime-local">` value. */
export const toLocalInput = (iso: string) => iso.slice(0, 16);
