import type { FileCategory, FileNode, StorageStat } from "@/lib/types";

const MB = 1024 * 1024;
const GB = 1024 * MB;

export const files: FileNode[] = [
  {
    id: "f-1",
    name: "Documents",
    kind: "folder",
    sizeBytes: 1.1 * MB,
    modifiedAt: new Date(Date.now() - 59 * 60 * 1000),
    shared: true,
  },
  {
    id: "f-2",
    name: "Photos",
    kind: "folder",
    sizeBytes: 18 * GB,
    modifiedAt: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000),
    shared: true,
  },
  {
    id: "f-3",
    name: "Vidéos",
    kind: "folder",
    sizeBytes: 0,
    modifiedAt: new Date(Date.now() - 6 * 365 * 24 * 60 * 60 * 1000),
    shared: true,
  },
  {
    id: "f-4",
    name: "Recette.txt",
    kind: "file",
    sizeBytes: 28 * 1024,
    modifiedAt: new Date(Date.now() - 30 * 1000),
    shared: true,
  },
  {
    id: "f-5",
    name: "Inscription.pdf",
    kind: "file",
    sizeBytes: 200 * 1024,
    modifiedAt: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000),
    shared: true,
  },
  {
    id: "f-6",
    name: "AG-10-09-2022.mp4",
    kind: "file",
    sizeBytes: 1.2 * GB,
    modifiedAt: new Date(Date.now() - 4 * 365 * 24 * 60 * 60 * 1000),
    shared: true,
  },
];

export const fileCategories: FileCategory[] = [
  "Tous les fichiers",
  "Favoris",
  "Arbre de fichier",
  "Fichiers personnels",
  "Fichiers partagés",
  "Récents",
  "Catégories",
];

export const storageStats: StorageStat[] = [
  { label: "Stockage total", usedGb: 250, totalGb: 1000 },
  { label: "Documents", usedGb: 40, totalGb: 250 },
  { label: "Photos", usedGb: 180, totalGb: 500 },
  { label: "Vidéos", usedGb: 30, totalGb: 250 },
];
