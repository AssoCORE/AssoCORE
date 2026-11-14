import { UsersSearch } from "@/components/custom/users-search";
import { StatCard } from "@/components/custom/stat-card";
import { UsersTable } from "@/components/custom/users-table";
import { Card, CardContent } from "@/components/ui/card";
import { listUsers } from "@/lib/auth/admin";
import { ROLE_ADMIN, ROLE_STAFF } from "@/lib/auth/roles";

export default async function AdminUserPage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string; role?: string }>;
}) {
  const { q, role } = await searchParams;

  // Counts read `total` with limit=1; the backend filters by role in SQL.
  const [page, all, staff, admins] = await Promise.all([
    listUsers({ q, role, limit: 200 }),
    listUsers({ limit: 1 }),
    listUsers({ role: ROLE_STAFF, limit: 1 }),
    listUsers({ role: ROLE_ADMIN, limit: 1 }),
  ]);

  return (
    <div className="flex flex-1 flex-col gap-4 md:gap-6">
      <div className="grid gap-4 md:gap-6 sm:grid-cols-3">
        <StatCard label="Adhérents" value={all?.total ?? "—"} />
        <StatCard label="Staff" value={staff?.total ?? "—"} accent="primary" />
        <StatCard label="Admins" value={admins?.total ?? "—"} />
      </div>

      <UsersSearch />

      <Card className="min-h-0 flex-1">
        <CardContent className="h-full overflow-y-auto p-0">
          {!page ? (
            <p className="p-4 text-sm text-destructive">Impossible de charger les adhérents.</p>
          ) : (
            <>
              <UsersTable users={page.items} />
              {page.total > page.items.length && (
                <p className="px-4 py-2 text-xs text-muted-foreground">
                  {page.items.length} affichés sur {page.total} — affinez la recherche.
                </p>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
