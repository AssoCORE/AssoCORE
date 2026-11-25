import Link from "next/link";
import { redirect } from "next/navigation";

import { AccountSettings } from "@/components/custom/account-settings";
import { ProfileForm } from "@/components/custom/profile-form";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Card, CardContent } from "@/components/ui/card";
import { apiJson } from "@/lib/api";
import { getCurrentUser } from "@/lib/auth/session";
import { fullName, initialsOf, labelOf } from "@/lib/roles";
import type { EventOut, NcLinkStatus, Page, ReminderOut } from "@/lib/types";

export default async function ProfilePage() {
  const user = await getCurrentUser();
  if (!user) redirect("/login");

  // Counts come from `total` with limit=1 — no dedicated stats endpoint exists.
  const [registered, upcoming, reminders, ncLink] = await Promise.all([
    apiJson<Page<EventOut>>("/event/?my_events=true&limit=1").catch(() => null),
    apiJson<Page<EventOut>>(
      "/event/?my_events=true&upcoming=true&limit=1"
    ).catch(() => null),
    apiJson<Page<ReminderOut>>("/user/reminder/?upcoming=true&limit=1").catch(
      () => null
    ),
    apiJson<NcLinkStatus>("/nextcloud/link").catch(() => null),
  ]);

  return (
    <div className="flex flex-1 flex-col gap-4 md:gap-6">
      <Card className="overflow-hidden p-0">
        <div className="h-40 w-full bg-gradient-to-r from-sky-300 via-teal-300 to-emerald-400" />
      </Card>

      <div className="grid flex-1 min-h-0 auto-rows-fr gap-4 md:gap-6 lg:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)]">
        <Card className="h-full">
          <CardContent className="flex h-full flex-col gap-6 overflow-y-auto p-6">
            <header className="flex items-center gap-4">
              <Avatar className="size-16 border-4 border-card shadow-md">
                <AvatarFallback className="bg-primary text-xl font-bold text-primary-foreground">
                  {initialsOf(user.firstname, user.name)}
                </AvatarFallback>
              </Avatar>
              <div className="flex flex-1 flex-col">
                <h1 className="text-xl font-semibold">{fullName(user)}</h1>
                <p className="text-sm text-muted-foreground">{user.mail}</p>
                <span className="mt-1 inline-flex w-fit text-xs font-medium text-role-user underline decoration-2 underline-offset-4">
                  {user.roles.map(labelOf).join(", ") || "Aucun rôle"}
                </span>
              </div>
            </header>

            <ProfileForm user={user} />
            <AccountSettings link={ncLink} />
          </CardContent>
        </Card>

        <Card className="h-full">
          <CardContent className="flex h-full flex-col gap-4 overflow-y-auto p-6">
            <h2 className="text-lg font-semibold">Statistiques :</h2>
            <StatRow
              label="Inscriptions à des évènements"
              value={registered?.total ?? "—"}
            />
            <StatRow
              label="Évènements à venir"
              value={upcoming?.total ?? "—"}
            />
            <StatRow
              label="Rappels à venir"
              value={
                <Link href="/calendar" className="hover:underline">
                  {reminders?.total ?? "—"}
                </Link>
              }
            />
          </CardContent>
        </Card>
      </div>

      <div className="flex items-center justify-between border-t border-border pt-4 text-sm">
        {/* biome-ignore lint/a11y/useValidAnchor: placeholder until the privacy policy page (#202) exists */}
        <a href="#" className="font-medium text-primary hover:underline">
          Mentions légales
        </a>
        {/* biome-ignore lint/a11y/useValidAnchor: placeholder until the association charter page exists */}
        <a href="#" className="font-medium text-primary hover:underline">
          Charte de l&apos;association
        </a>
      </div>
    </div>
  );
}

function StatRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-0.5 border-b border-border pb-3 last:border-0 last:pb-0">
      <span className="text-xs text-muted-foreground">{label} :</span>
      <span className="text-2xl font-bold">{value}</span>
    </div>
  );
}
