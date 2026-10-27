import type { Activity, Event } from "@/lib/types";

export const events: Event[] = [
  {
    id: "evt-1",
    title: "Vente de crêpe",
    description:
      "Venez aider à participer au financement de voyage annuel de l'association.",
    startsAt: new Date("2026-03-22T14:00:00"),
    endsAt: new Date("2026-03-22T18:00:00"),
    location: "Rennes, France",
    participants: { current: 5, max: 15 },
    price: "Gratuit",
    category: { label: "Autofinancement", tone: "amber" },
  },
  {
    id: "evt-2",
    title: "Atelier fabrication de marionnettes",
    description:
      "Atelier créatif de fabrication de marionnettes. Repartez avec votre création.",
    startsAt: new Date("2026-04-01T13:00:00"),
    endsAt: new Date("2026-04-01T17:00:00"),
    location: "Rennes, France",
    participants: { current: 5, max: 10 },
    price: 5,
    category: { label: "Atelier", tone: "purple" },
  },
  {
    id: "evt-3",
    title: "Café rencontre",
    description:
      "Venez découvrir la culture malgache au travers d'un café rencontre convivial.",
    startsAt: new Date("2026-06-30T19:00:00"),
    endsAt: new Date("2026-06-30T21:00:00"),
    location: "Rennes, France",
    participants: { current: 18, max: 20 },
    price: "Gratuit",
    category: { label: "Culture culinaire", tone: "red" },
  },
  {
    id: "evt-4",
    title: "Atelier Cosplay",
    description: "Atelier de découverte du cosplay avec des costumes à essayer.",
    startsAt: new Date("2026-07-24T14:00:00"),
    endsAt: new Date("2026-07-25T18:00:00"),
    location: "Rennes, France",
    participants: { current: 8, max: 20 },
    price: 10,
    category: { label: "Atelier", tone: "amber" },
  },
];

export const recentActivity: Activity[] = [
  {
    id: "act-1",
    actor: "Jean Jack",
    verb: "a créé",
    targetKind: "l'événement",
    target: "Vente de crêpe",
  },
  {
    id: "act-2",
    actor: "Jean Louis",
    verb: "a rejoint",
    targetKind: "l'événement",
    target: "Atelier fabrication de marionnettes",
  },
  {
    id: "act-3",
    actor: "Jean Claude",
    verb: "a créé",
    targetKind: "l'événement",
    target: "Café rencontre",
  },
  {
    id: "act-4",
    actor: "Jean Marc",
    verb: "a rejoint",
    targetKind: "l'événement",
    target: "Atelier Cosplay",
  },
];
