import { format, formatDistanceToNow, isSameDay } from "date-fns";
import { fr } from "date-fns/locale";

export function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  const value = bytes / 1024 ** i;
  const formatted = value >= 10 || i === 0 ? Math.round(value).toString() : value.toFixed(1);
  return `${formatted} ${units[i]}`;
}

export function formatRelativeFromNow(date: Date): string {
  return "Il y a " + formatDistanceToNow(date, { locale: fr });
}

export function formatEuros(amount: number): string {
  return new Intl.NumberFormat("fr-FR", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 0,
  }).format(amount);
}

export function formatEventRange(
  event: { start_date: string; end_date: string },
  dayFormat = "d MMMM yyyy",
): string {
  const start = new Date(event.start_date);
  const end = new Date(event.end_date);
  const day = format(start, dayFormat, { locale: fr });
  if (isSameDay(start, end)) {
    return `${day} · ${format(start, "HH:mm")} à ${format(end, "HH:mm")}`;
  }
  return `${day} ${format(start, "HH:mm")} → ${format(end, dayFormat, { locale: fr })} ${format(end, "HH:mm")}`;
}
