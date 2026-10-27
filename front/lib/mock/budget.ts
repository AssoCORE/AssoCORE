import type { BudgetRequest } from "@/lib/types";

export const budgetTotals = {
  Total: 12450,
  Événements: 4200,
  Matériel: 3100,
  Autres: 5150,
} as const;

export type BudgetCategory = keyof typeof budgetTotals;

const now = Date.now();
const daysAgo = (n: number) => new Date(now - n * 24 * 60 * 60 * 1000);

export const pendingRequests: BudgetRequest[] = [
  { id: "br-1", date: daysAgo(1), name: "Achat de tissu", reason: "Atelier", amountEur: 120 },
  { id: "br-2", date: daysAgo(2), name: "Location salle", reason: "AG", amountEur: 450 },
  { id: "br-3", date: daysAgo(3), name: "Café rencontre", reason: "Boissons", amountEur: 80 },
  { id: "br-4", date: daysAgo(4), name: "Impression flyers", reason: "Com", amountEur: 60 },
  { id: "br-5", date: daysAgo(5), name: "Peinture", reason: "Atelier", amountEur: 45 },
  { id: "br-6", date: daysAgo(6), name: "Snacks événement", reason: "Vente", amountEur: 210 },
  { id: "br-7", date: daysAgo(7), name: "Achat instruments", reason: "Musique", amountEur: 380 },
  { id: "br-8", date: daysAgo(8), name: "Transport", reason: "Sortie", amountEur: 150 },
];

export const historyRequests: BudgetRequest[] = [
  { id: "bh-1", date: daysAgo(10), name: "Réparation matériel", reason: "Divers", amountEur: 95 },
  { id: "bh-2", date: daysAgo(15), name: "Achat papier", reason: "Bureau", amountEur: 30 },
  { id: "bh-3", date: daysAgo(20), name: "Café atelier", reason: "Boissons", amountEur: 25 },
  { id: "bh-4", date: daysAgo(28), name: "Impression affiches", reason: "Com", amountEur: 110 },
  { id: "bh-5", date: daysAgo(35), name: "Achat gâteaux", reason: "Vente", amountEur: 75 },
  { id: "bh-6", date: daysAgo(42), name: "Location vidéoprojecteur", reason: "AG", amountEur: 90 },
  { id: "bh-7", date: daysAgo(58), name: "Achat tickets", reason: "Sortie", amountEur: 260 },
  { id: "bh-8", date: daysAgo(72), name: "Fournitures", reason: "Bureau", amountEur: 40 },
];
