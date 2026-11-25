"use client";

import { Search, SlidersHorizontal } from "lucide-react";
import type { ReactNode } from "react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

export function SearchBar({
  placeholder = "Search (Ctrl+/)",
  value,
  onChange,
  onFilterClick,
  filters,
  filterActive = false,
  className,
}: {
  placeholder?: string;
  value?: string;
  onChange?: (v: string) => void;
  onFilterClick?: () => void;
  /** Dropdown content opened by the filter button (takes precedence over `onFilterClick`). */
  filters?: ReactNode;
  /** Highlights the filter button while a non-default filter applies. */
  filterActive?: boolean;
  className?: string;
}) {
  const filterButton = (
    <Button
      type="button"
      variant="ghost"
      size="icon"
      className={cn("text-muted-foreground", filterActive && "text-primary")}
      onClick={filters ? undefined : onFilterClick}
      aria-label="Filtres"
    >
      <SlidersHorizontal className="size-4" />
    </Button>
  );

  return (
    <div
      className={cn(
        "flex items-center gap-2 rounded-md bg-card p-2 shadow-sm",
        className
      )}
    >
      <div className="relative flex-1">
        <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          type="search"
          placeholder={placeholder}
          value={value}
          onChange={(e) => onChange?.(e.target.value)}
          className="h-10 border-transparent bg-transparent pl-9 shadow-none focus-visible:ring-0"
        />
      </div>
      {filters ? (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>{filterButton}</DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            {filters}
          </DropdownMenuContent>
        </DropdownMenu>
      ) : (
        filterButton
      )}
    </div>
  );
}
