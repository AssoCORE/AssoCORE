import { ChevronLeft, FileText, Folder, User } from "lucide-react";
import Link from "next/link";

import { StatCard } from "@/components/custom/stat-card";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { apiJson, query } from "@/lib/api";
import { formatBytes } from "@/lib/format";
import type { AdminFileEntry } from "@/lib/types";
import { cn } from "@/lib/utils";

const trim = (p: string) => p.replace(/^\/+|\/+$/g, "");
const href = (user: string, path = "") => `/adminEvent${query({ user, path: trim(path) })}`;

// Admin view over every member's Nextcloud storage. Both endpoints are gated by
// require_admin on the backend router itself.
export default async function AdminFilesPage({
  searchParams,
}: {
  searchParams: Promise<{ user?: string; path?: string }>;
}) {
  const { user, path = "" } = await searchParams;

  const ncUsers = await apiJson<{ users: string[] }>("/nextcloud/users").catch(() => null);
  const files = user
    ? await apiJson<{ files: AdminFileEntry[] }>(
        `/nextcloud/files/${encodeURIComponent(user)}${query({ path })}`,
      ).catch(() => null)
    : null;

  const current = trim(path);
  const parent = current.split("/").slice(0, -1).join("/");
  const entries = files?.files ?? [];
  const totalBytes = entries.reduce((s, f) => s + f.size, 0);

  return (
    <div className="flex flex-1 flex-col gap-4 md:gap-6">
      <div className="grid gap-4 md:gap-6 sm:grid-cols-3">
        <StatCard label="Comptes Nextcloud :" value={ncUsers?.users.length ?? "—"} />
        <StatCard label="Éléments dans ce dossier :" value={user ? entries.length : "—"} />
        <StatCard
          label="Taille de ce dossier :"
          value={user ? formatBytes(totalBytes) : "—"}
          accent="primary"
        />
      </div>

      <div className="grid flex-1 min-h-0 auto-rows-fr gap-4 md:gap-6 lg:grid-cols-[minmax(0,260px)_minmax(0,1fr)]">
        <Card className="h-full min-h-0">
          <CardContent className="flex h-full flex-col gap-1 overflow-y-auto p-3">
            {!ncUsers ? (
              <p className="p-2 text-sm text-destructive">Nextcloud est indisponible.</p>
            ) : (
              ncUsers.users.map((u) => (
                <Link
                  key={u}
                  href={href(u)}
                  className={cn(
                    "flex items-center gap-2.5 rounded-md px-3 py-2 text-sm transition hover:bg-primary/5",
                    u === user && "bg-primary/10 font-medium text-primary",
                  )}
                >
                  <User className="size-4" />
                  <span className="truncate">{u}</span>
                </Link>
              ))
            )}
          </CardContent>
        </Card>

        <Card className="h-full min-h-0">
          <CardContent className="flex h-full flex-col p-0">
            <div className="flex items-center gap-2 border-b border-border px-4 py-2 text-sm">
              {user && current && (
                <Button asChild variant="ghost" size="icon-sm" aria-label="Dossier parent">
                  <Link href={href(user, parent)}>
                    <ChevronLeft />
                  </Link>
                </Button>
              )}
              <span className="truncate font-medium">
                {user ? `${user} : /${current}` : "Sélectionnez un compte"}
              </span>
            </div>
            <div className="flex-1 overflow-y-auto">
              {user && !files ? (
                <p className="p-4 text-sm text-destructive">Impossible de lister ce dossier.</p>
              ) : user ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Nom</TableHead>
                      <TableHead className="w-28 text-right">Taille</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {entries.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={2} className="text-center text-muted-foreground">
                          Dossier vide.
                        </TableCell>
                      </TableRow>
                    )}
                    {entries.map((f) => (
                      <TableRow key={f.name}>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            {f.is_dir ? (
                              <Folder className="size-4 text-muted-foreground" />
                            ) : (
                              <FileText className="size-4 text-muted-foreground" />
                            )}
                            {f.is_dir ? (
                              <Link
                                href={href(user, [current, f.name].filter(Boolean).join("/"))}
                                className="truncate hover:underline"
                              >
                                {f.name}
                              </Link>
                            ) : (
                              <span className="truncate">{f.name}</span>
                            )}
                          </div>
                        </TableCell>
                        <TableCell className="text-right tabular-nums">
                          {formatBytes(f.size)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : null}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
