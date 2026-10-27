"use client";

import { MoreVertical } from "lucide-react";
import { format } from "date-fns";
import { fr } from "date-fns/locale";

import { DataTable, type DataTableColumn } from "@/components/custom/data-table";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { User, UserRole } from "@/lib/types";

const roleToneClass: Record<UserRole, string> = {
  Utilisateur: "text-role-user decoration-role-user",
  Admin: "text-role-admin decoration-role-admin",
  Trésorier: "text-role-tresorier decoration-role-tresorier",
  Président: "text-role-president decoration-role-president",
};

const initialsOf = (name: string) =>
  name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

const columns: DataTableColumn<User>[] = [
  {
    key: "user",
    header: "Utilisateur",
    render: (u) => (
      <div className="flex items-center gap-3">
        <Avatar className="size-8">
          <AvatarFallback className="bg-primary text-xs font-semibold text-primary-foreground">
            {initialsOf(u.fullName)}
          </AvatarFallback>
        </Avatar>
        <span className="font-medium">{u.fullName}</span>
      </div>
    ),
  },
  {
    key: "email",
    header: "Email",
    render: (u) => <span className="text-muted-foreground">{u.email}</span>,
  },
  {
    key: "role",
    header: "Rôle",
    render: (u) => (
      <span
        className={cn(
          "font-medium underline decoration-2 underline-offset-4",
          roleToneClass[u.role],
        )}
      >
        {u.role}
      </span>
    ),
  },
  {
    key: "status",
    header: "Status",
    render: (u) => (
      <span
        className={cn(
          "font-semibold",
          u.status === "Actif" ? "text-primary" : "text-brand-red",
        )}
      >
        {u.status}
      </span>
    ),
  },
  {
    key: "createdAt",
    header: "Date de création",
    render: (u) => (
      <span className="tabular-nums">{format(u.createdAt, "d MMM yyyy", { locale: fr })}</span>
    ),
  },
  {
    key: "actions",
    header: "Actions",
    render: () => (
      <Button variant="ghost" size="icon" aria-label="Actions">
        <MoreVertical className="size-4" />
      </Button>
    ),
    className: "w-16 text-right",
    headerClassName: "w-16 text-right",
  },
];

export function UsersTable({ users }: { users: User[] }) {
  return <DataTable columns={columns} data={users} rowKey={(u) => u.id} />;
}
