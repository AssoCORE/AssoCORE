import { FileText, Star } from "lucide-react";
import Link from "next/link";
import type { ComponentType } from "react";

import { cn } from "@/lib/utils";

// Only the views the storage API can serve: GET /storage/ and GET /storage/favourites.
export type FileView = "all" | "favourites";

const views: {
  key: FileView;
  label: string;
  href: string;
  icon: ComponentType<{ className?: string }>;
}[] = [
  { key: "all", label: "Tous les fichiers", href: "/file", icon: FileText },
  {
    key: "favourites",
    label: "Favoris",
    href: "/file?view=favourites",
    icon: Star,
  },
];

export function FileCategoryList({ active }: { active: FileView }) {
  return (
    <nav className="flex flex-col gap-1">
      {views.map(({ key, label, href, icon: Icon }) => (
        <Link
          key={key}
          href={href}
          className={cn(
            "flex items-center gap-2.5 rounded-md px-3 py-2 text-sm text-foreground transition hover:bg-primary/5",
            key === active && "bg-primary/10 font-medium text-primary"
          )}
        >
          <Icon className="size-4" />
          {label}
        </Link>
      ))}
    </nav>
  );
}
