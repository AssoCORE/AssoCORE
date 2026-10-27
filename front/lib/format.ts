import { formatDistanceToNow } from "date-fns";
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
