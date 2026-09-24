import { listUsers } from "@/lib/auth/admin";

// RBAC proof: this renders only because the admin layout let us through
// (frontend gate), and listUsers() itself calls the backend's admin-only
// GET /user/ (require_admin — real, server-side enforcement).
export default async function AdminPage() {
  const page = await listUsers();

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Admin — all users</h1>
      {!page ? (
        <p className="text-destructive">Failed to load users.</p>
      ) : (
        <>
          <p className="text-muted-foreground text-sm">
            Showing {page.items.length} of {page.total}
          </p>
          <ul className="space-y-1 font-mono text-sm">
            {page.items.map((u) => (
              <li key={u.id}>
                {u.username} —{" "}
                {u.roles.map((r) => r.name).join(", ") || "no roles"}
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
