"use client";

import { format } from "date-fns";
import { fr } from "date-fns/locale";
import { BellPlus, ChevronLeft, Folder, Trash2 } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { deleteUser, sendNotification } from "@/lib/actions";
import { fullName, initialsOf, labelOf, roleToneClass } from "@/lib/roles";
import { notificationMessageError } from "@/lib/schemas";
import type { UserOut } from "@/lib/types";
import { cn } from "@/lib/utils";

type Profile = Omit<UserOut, "notifications" | "reminders">;

export function UserDetail({
  user,
  unread,
  reminders,
}: {
  user: Profile;
  unread: number;
  reminders: number;
}) {
  const me = useAuth();
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(
    null
  );

  function onNotify() {
    const text = window.prompt(`Message pour ${fullName(user)}`)?.trim();
    if (!text) return;
    const invalid = notificationMessageError(text);
    if (invalid) {
      setMessage({ ok: false, text: invalid });
      return;
    }
    setMessage(null);
    startTransition(async () => {
      const res = await sendNotification(user.id, text);
      setMessage(
        res.ok
          ? { ok: true, text: "Notification envoyée." }
          : { ok: false, text: res.error }
      );
    });
  }

  function onDelete() {
    if (
      !window.confirm(
        `Supprimer définitivement ${fullName(user)} (et son compte Nextcloud) ?`
      )
    ) {
      return;
    }
    setMessage(null);
    startTransition(async () => {
      const res = await deleteUser(user.id);
      if (res.ok) router.push("/adminUser");
      else setMessage({ ok: false, text: res.error });
    });
  }

  return (
    <div className="flex flex-1 flex-col gap-4 md:gap-6">
      <Button asChild variant="ghost" size="sm" className="self-start">
        <Link href="/adminUser">
          <ChevronLeft />
          Tous les adhérents
        </Link>
      </Button>

      <div className="grid flex-1 min-h-0 grid-cols-[minmax(0,1fr)] gap-4 md:gap-6 lg:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)]">
        <Card className="h-full">
          <CardContent className="flex h-full flex-col gap-6 p-6">
            <header className="flex items-center gap-4">
              <Avatar className="size-16 border-4 border-card shadow-md">
                <AvatarFallback className="bg-primary text-xl font-bold text-primary-foreground">
                  {initialsOf(user.firstname, user.name)}
                </AvatarFallback>
              </Avatar>
              <div className="flex min-w-0 flex-1 flex-col">
                <h1 className="truncate text-xl font-semibold">
                  {fullName(user)}
                </h1>
                <p className="truncate text-sm text-muted-foreground">
                  @{user.username}
                </p>
                <div className="mt-1 flex flex-wrap gap-2 text-xs">
                  {user.roles.length === 0 && (
                    <span className="text-muted-foreground">Aucun rôle</span>
                  )}
                  {user.roles.map((r) => (
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
              </div>
            </header>

            <dl className="grid gap-4 text-sm sm:grid-cols-2">
              <Field label="Email">{user.mail}</Field>
              <Field label="Téléphone">{user.phone ?? "—"}</Field>
              <Field label="Date de naissance">
                {user.birth_date
                  ? format(new Date(user.birth_date), "d MMMM yyyy", {
                      locale: fr,
                    })
                  : "—"}
              </Field>
              <Field label="Identifiant">n°{user.id}</Field>
            </dl>

            <div className="flex flex-wrap gap-2 border-t border-border pt-4">
              <Button
                variant="outline"
                size="sm"
                onClick={onNotify}
                disabled={pending}
              >
                <BellPlus />
                Envoyer une notification
              </Button>
              <Button asChild variant="outline" size="sm">
                <Link
                  href={`/adminEvent?${new URLSearchParams({ user: user.username })}`}
                >
                  <Folder />
                  Voir ses dossiers
                </Link>
              </Button>
              {user.id !== me.id && (
                <Button
                  variant="outline"
                  size="sm"
                  className="text-brand-red hover:text-brand-red"
                  onClick={onDelete}
                  disabled={pending}
                >
                  <Trash2 />
                  Supprimer
                </Button>
              )}
            </div>
            {message && (
              <p
                className={
                  message.ok
                    ? "text-sm text-primary"
                    : "text-sm text-destructive"
                }
              >
                {message.text}
              </p>
            )}
          </CardContent>
        </Card>

        <Card className="h-full">
          <CardContent className="flex h-full flex-col gap-4 p-6">
            <h2 className="text-lg font-semibold">Statistiques :</h2>
            <Stat label="Notifications non lues" value={unread} />
            <Stat label="Rappels" value={reminders} />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-0.5">
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className="truncate font-medium">{children}</dd>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-0.5 border-b border-border pb-3 last:border-0 last:pb-0">
      <span className="text-xs text-muted-foreground">{label} :</span>
      <span className="text-2xl font-bold">{value}</span>
    </div>
  );
}
