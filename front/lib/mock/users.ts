import type { Profile, User } from "@/lib/types";

export const users: User[] = [
  {
    id: "u-1",
    fullName: "Jean Michel",
    email: "jean.michel@exemple.fr",
    role: "Utilisateur",
    status: "Actif",
    createdAt: new Date("2024-01-15"),
  },
  {
    id: "u-2",
    fullName: "Jean Paul",
    email: "jean.paul@exemple.fr",
    role: "Utilisateur",
    status: "Inactif",
    createdAt: new Date("2024-01-28"),
  },
  {
    id: "u-3",
    fullName: "Jean Jack",
    email: "jean.jack@exemple.fr",
    role: "Admin",
    status: "Actif",
    createdAt: new Date("2024-02-05"),
  },
  {
    id: "u-4",
    fullName: "Jean Claude",
    email: "jean.claude@exemple.fr",
    role: "Trésorier",
    status: "Actif",
    createdAt: new Date("2024-02-12"),
  },
  {
    id: "u-5",
    fullName: "Jean Marc",
    email: "jean.marc@exemple.fr",
    role: "Utilisateur",
    status: "Inactif",
    createdAt: new Date("2024-02-18"),
  },
  {
    id: "u-6",
    fullName: "Jean Louis",
    email: "jean.louis@exemple.fr",
    role: "Président",
    status: "Actif",
    createdAt: new Date("2024-03-02"),
  },
  {
    id: "u-7",
    fullName: "Jean Bon",
    email: "jean.bon@exemple.fr",
    role: "Admin",
    status: "Actif",
    createdAt: new Date("2024-03-08"),
  },
];

export const currentProfile: Profile = {
  username: "Jean Michel",
  fullName: "Jean Michel",
  email: "jean.michel@exemple.fr",
  phone: "+33 6 12 34 56 78",
  role: "Utilisateur",
  memberSince: new Date("2019-06-01"),
  participations: 24,
  volunteering: 15,
};

export const userStats = {
  total: users.length + 14,
  active: users.filter((u) => u.status === "Actif").length + 12,
  admins: users.filter((u) => u.role === "Admin").length + 1,
  members: 21,
};
