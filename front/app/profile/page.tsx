"use client";

import { Settings } from "lucide-react";
import { format } from "date-fns";
import { fr } from "date-fns/locale";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { currentProfile } from "@/lib/mock/users";

export default function ProfilePage() {
  const initials = currentProfile.fullName
    .split(" ")
    .map((s) => s[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
  const memberSince = format(currentProfile.memberSince, "MMMM yyyy", { locale: fr });

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
                  {initials}
                </AvatarFallback>
              </Avatar>
              <div className="flex flex-1 flex-col">
                <h1 className="text-xl font-semibold">{currentProfile.fullName}</h1>
                <p className="text-sm text-muted-foreground">{currentProfile.email}</p>
                <span className="mt-1 inline-flex w-fit text-xs font-medium text-role-user underline decoration-2 underline-offset-4">
                  {currentProfile.role}
                </span>
              </div>
              <Button variant="ghost" size="icon" aria-label="Paramètres">
                <Settings className="size-5" />
              </Button>
            </header>

            <form className="grid gap-4 sm:grid-cols-2">
              <FormField id="username" label="Utilisateur" defaultValue={currentProfile.username} />
              <FormField id="fullName" label="Nom" defaultValue={currentProfile.fullName} />
              <FormField
                id="email"
                label="Email"
                type="email"
                defaultValue={currentProfile.email}
              />
              <FormField
                id="phone"
                label="Téléphone"
                type="tel"
                defaultValue={currentProfile.phone}
              />
              <FormField id="password" label="Nouveau mot de passe" type="password" />
              <FormField
                id="password-confirm"
                label="Confirmer le nouveau mot de passe"
                type="password"
              />
              <div className="sm:col-span-2">
                <Button type="submit" className="w-full sm:w-auto">
                  Enregistrer les modifications
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        <Card className="h-full">
          <CardContent className="flex h-full flex-col gap-4 overflow-y-auto p-6">
            <h2 className="text-lg font-semibold">Statistiques :</h2>
            <StatRow label="Participation à des évènements" value={currentProfile.participations} />
            <StatRow label="Bénévolat dans des évènements" value={currentProfile.volunteering} />
            <StatRow label="Membre depuis" value={memberSince} />
          </CardContent>
        </Card>
      </div>

      <div className="flex items-center justify-between border-t border-border pt-4 text-sm">
        <a href="#" className="font-medium text-primary hover:underline">
          Mentions légales
        </a>
        <a href="#" className="font-medium text-primary hover:underline">
          Charte de l&apos;association
        </a>
      </div>
    </div>
  );
}

function FormField({
  id,
  label,
  ...rest
}: {
  id: string;
  label: string;
  type?: string;
  defaultValue?: string;
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <Label htmlFor={id} className="text-xs font-medium text-muted-foreground">
        {label}
      </Label>
      <Input id={id} {...rest} />
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
