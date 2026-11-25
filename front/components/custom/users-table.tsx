"use client";

import { BellPlus, MoreVertical, Trash2 } from "lucide-react";
import Link from "next/link";
import { useState, useTransition } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import {
  DataTable,
  type DataTableColumn,
} from "@/components/custom/data-table";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { deleteUser, sendNotification } from "@/lib/actions";
import { fullName, initialsOf, labelOf, roleToneClass } from "@/lib/roles";
import { notificationMessageError } from "@/lib/schemas";
import type { UserOut } from "@/lib/types";
import { cn } from "@/lib/utils";

export function UsersTable({ users }: { users: UserOut[] }) {
  const me = useAuth();
  const [pending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  function onNotify(user: UserOut) {
    const message = window.prompt(`Message pour ${fullName(user)}`)?.trim();
    if (!message) return;
    setNotice(null);
    const invalid = notificationMessageError(message);
    setError(invalid);
    if (invalid) return;
    startTransition(async () => {
      const res = await sendNotification(user.id, message);
      if (res.ok) setNotice(`Notification envoyée à ${fullName(user)}.`);
      else setError(res.error);
    });
  }

  function onDelete(user: UserOut) {
    if (
      !window.confirm(
        `Supprimer définitivement ${fullName(user)} (et son compte Nextcloud) ?`
      )
    ) {
      return;
    }
    setError(null);
    setNotice(null);
    startTransition(async () => {
      const res = await deleteUser(user.id);
      if (!res.ok) setError(res.error);
    });
  }

  const columns: DataTableColumn<UserOut>[] = [
    {
      key: "user",
      header: "Utilisateur",
      render: (u) => (
        <div className="flex items-center gap-3">
          <Avatar className="size-8">
            <AvatarFallback className="bg-primary text-xs font-semibold text-primary-foreground">
              {initialsOf(u.firstname, u.name)}
            </AvatarFallback>
          </Avatar>
          <div className="flex flex-col">
            <Link
              href={`/adminUser/${u.id}`}
              className="font-medium hover:underline"
            >
              {fullName(u)}
            </Link>
            <span className="text-xs text-muted-foreground">@{u.username}</span>
          </div>
        </div>
      ),
    },
    {
      key: "email",
      header: "Email",
      render: (u) => <span className="text-muted-foreground">{u.mail}</span>,
    },
    {
      key: "phone",
      header: "Téléphone",
      render: (u) => (
        <span className="tabular-nums text-muted-foreground">
          {u.phone ?? "—"}
        </span>
      ),
    },
    {
      key: "role",
      header: "Rôles",
      render: (u) => (
        <div className="flex flex-wrap gap-2">
          {u.roles.length === 0 && (
            <span className="text-muted-foreground">—</span>
          )}
          {u.roles.map((r) => (
            <span
              key={r.id}
              className={cn(
                "font-medium underline decoration-2 underline-offset-4",
                roleToneClass[r.name]
              )}
            >
              {labelOf(r)}
            </span>
          ))}
        </div>
      ),
    },
    {
      key: "actions",
      header: "Actions",
      render: (u) =>
        u.id === me.id ? null : (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                aria-label="Actions"
                disabled={pending}
              >
                <MoreVertical className="size-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onSelect={() => onNotify(u)}>
                <BellPlus className="mr-2 size-4" />
                Envoyer une notification
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                className="text-brand-red focus:text-brand-red"
                onSelect={() => onDelete(u)}
              >
                <Trash2 className="mr-2 size-4" />
                Supprimer
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        ),
      className: "w-16 text-right",
      headerClassName: "w-16 text-right",
    },
  ];

  return (
    <>
      {error && <p className="px-4 py-2 text-sm text-destructive">{error}</p>}
      {notice && <p className="px-4 py-2 text-sm text-primary">{notice}</p>}
      <DataTable columns={columns} data={users} rowKey={(u) => String(u.id)} />
    </>
  );
}
