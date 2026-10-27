"use client";

import {
  Clock,
  FileText,
  Folder,
  FolderTree,
  Share2,
  Star,
  Tag,
  User,
} from "lucide-react";
import type { ComponentType } from "react";
import type { FileCategory } from "@/lib/types";
import { cn } from "@/lib/utils";

const icons: Record<FileCategory, ComponentType<{ className?: string }>> = {
  "Tous les fichiers": FileText,
  Favoris: Star,
  "Arbre de fichier": FolderTree,
  "Fichiers personnels": User,
  "Fichiers partagés": Share2,
  Récents: Clock,
  Catégories: Tag,
};

export function FileCategoryList({
  categories,
  active,
  onSelect,
}: {
  categories: FileCategory[];
  active: FileCategory;
  onSelect: (cat: FileCategory) => void;
}) {
  return (
    <nav className="flex flex-col gap-1">
      {categories.map((cat) => {
        const Icon = icons[cat] ?? Folder;
        const isActive = cat === active;
        return (
          <button
            type="button"
            key={cat}
            onClick={() => onSelect(cat)}
            className={cn(
              "flex items-center gap-2.5 rounded-md px-3 py-2 text-sm text-foreground transition hover:bg-primary/5",
              isActive && "bg-primary/10 font-medium text-primary",
            )}
          >
            <Icon className="size-4" />
            {cat}
          </button>
        );
      })}
    </nav>
  );
}
