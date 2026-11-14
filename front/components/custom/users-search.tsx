"use client";

import { SearchBar } from "@/components/custom/search-bar";
import { useUrlSearch } from "@/hooks/use-url-search";

export function UsersSearch() {
  const search = useUrlSearch();
  return (
    <SearchBar
      value={search.value}
      onChange={search.setValue}
      placeholder="Rechercher par nom, utilisateur ou email"
    />
  );
}
