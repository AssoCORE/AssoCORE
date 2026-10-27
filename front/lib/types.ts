export type UserStatus = "Actif" | "Inactif";
export type UserRole = "Utilisateur" | "Admin" | "Trésorier" | "Président";

export type User = {
  id: string;
  fullName: string;
  email: string;
  role: UserRole;
  status: UserStatus;
  createdAt: Date;
  avatarUrl?: string;
};

export type EventCategory = {
  label: string;
  tone: "green" | "purple" | "red" | "blue" | "amber";
};

export type Event = {
  id: string;
  title: string;
  description: string;
  startsAt: Date;
  endsAt: Date;
  location: string;
  participants: { current: number; max: number };
  price: number | "Gratuit";
  imageUrl?: string;
  category: EventCategory;
};

export type Activity = {
  id: string;
  actor: string;
  verb: "a créé" | "a rejoint" | "a quitté";
  target: string;
  targetKind: "l'événement" | "le groupe";
};

export type FileNode = {
  id: string;
  name: string;
  kind: "folder" | "file";
  sizeBytes: number;
  modifiedAt: Date;
  shared?: boolean;
};

export type FileCategory =
  | "Tous les fichiers"
  | "Favoris"
  | "Arbre de fichier"
  | "Fichiers personnels"
  | "Fichiers partagés"
  | "Récents"
  | "Catégories";

export type StorageStat = {
  label: string;
  usedGb: number;
  totalGb: number;
};

export type BudgetRequest = {
  id: string;
  date: Date;
  name: string;
  reason: string;
  amountEur: number;
};

export type Profile = {
  username: string;
  fullName: string;
  email: string;
  phone: string;
  role: UserRole;
  memberSince: Date;
  participations: number;
  volunteering: number;
  bannerUrl?: string;
};
