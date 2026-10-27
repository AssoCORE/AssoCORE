"use client";

import { useMemo, useState } from "react";

import { SearchBar } from "@/components/custom/search-bar";
import { StatCard } from "@/components/custom/stat-card";
import { UsersTable } from "@/components/custom/users-table";
import { Card, CardContent } from "@/components/ui/card";
import { storageStats } from "@/lib/mock/files";
import { users } from "@/lib/mock/users";

export default function AdminEventPage() {
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return users;
    return users.filter((u) =>
      [u.fullName, u.email, u.role].join(" ").toLowerCase().includes(q),
    );
  }, [query]);

  return (
    <div className="flex flex-1 flex-col gap-4 md:gap-6">
      <div className="grid gap-4 md:gap-6 sm:grid-cols-2 xl:grid-cols-4">
        {storageStats.map((s) => (
          <StatCard
            key={s.label}
            label={`${s.label} :`}
            value={
              <span>
                {s.usedGb}
                <span className="text-lg text-muted-foreground">
                  /{s.totalGb}Go
                </span>
              </span>
            }
          />
        ))}
      </div>

      <SearchBar value={query} onChange={setQuery} />

      <Card className="min-h-0 flex-1">
        <CardContent className="h-full overflow-y-auto p-0">
          <UsersTable users={filtered} />
        </CardContent>
      </Card>
    </div>
  );
}
