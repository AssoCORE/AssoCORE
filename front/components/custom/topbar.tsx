"use client";

import { Bell, LogOut, Moon, Sun, User as UserIcon } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTheme } from "next-themes";
import { Fragment, useEffect, useState } from "react";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { currentProfile } from "@/lib/mock/users";

const ROOT_LABEL = "AssoName";

const segmentLabel: Record<string, string> = {
  event: "Évènements",
  calendar: "Calendrier",
  file: "Dossiers",
  profile: "Profil",
  adminUser: "Gestionnaire d'Adhérent",
  adminEvent: "Gestionnaire-Dossier",
  budget: "Budget",
};

function humanize(segment: string) {
  return segmentLabel[segment] ?? segment.replace(/-/g, " ");
}

export function TopBar() {
  const pathname = usePathname();
  const segments = pathname.split("/").filter(Boolean);
  const trail = segments.map((seg, idx) => ({
    label: humanize(seg),
    href: "/" + segments.slice(0, idx + 1).join("/"),
  }));

  return (
    <header className="sticky top-0 z-10 flex h-14 items-center justify-between gap-2 border-b border-border bg-card px-4 md:px-6">
      <div className="flex min-w-0 items-center gap-2">
        <Breadcrumb className="min-w-0">
        <BreadcrumbList className="flex-nowrap text-sm">
          <BreadcrumbItem className="hidden sm:inline-flex">
            <BreadcrumbLink asChild>
              <Link href="/" className="font-medium underline underline-offset-4">
                {ROOT_LABEL}
              </Link>
            </BreadcrumbLink>
          </BreadcrumbItem>
          {trail.length === 0 && (
            <>
              <BreadcrumbSeparator className="hidden sm:inline-flex" />
              <BreadcrumbItem>
                <BreadcrumbPage className="truncate font-medium underline underline-offset-4">
                  Accueil
                </BreadcrumbPage>
              </BreadcrumbItem>
            </>
          )}
          {trail.map((crumb, idx) => (
            <Fragment key={crumb.href}>
              <BreadcrumbSeparator className="hidden sm:inline-flex" />
              <BreadcrumbItem>
                {idx === trail.length - 1 ? (
                  <BreadcrumbPage className="truncate font-medium underline underline-offset-4">
                    {crumb.label}
                  </BreadcrumbPage>
                ) : (
                  <BreadcrumbLink asChild>
                    <Link href={crumb.href} className="truncate">
                      {crumb.label}
                    </Link>
                  </BreadcrumbLink>
                )}
              </BreadcrumbItem>
            </Fragment>
          ))}
        </BreadcrumbList>
      </Breadcrumb>
      </div>

      <div className="flex shrink-0 items-center gap-1 sm:gap-2">
        <ThemeToggle />
        <Button variant="ghost" size="icon" aria-label="Notifications">
          <Bell className="size-5" />
        </Button>
        <UserMenu />
      </div>
    </header>
  );
}

function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  const isDark = resolvedTheme === "dark";
  return (
    <Button
      variant="ghost"
      size="icon"
      aria-label="Basculer le thème"
      onClick={() => setTheme(isDark ? "light" : "dark")}
    >
      {mounted ? (
        isDark ? (
          <Sun className="size-5" />
        ) : (
          <Moon className="size-5" />
        )
      ) : (
        <Moon className="size-5 opacity-0" />
      )}
    </Button>
  );
}

function UserMenu() {
  const initials = currentProfile.fullName
    .split(" ")
    .map((s) => s[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          type="button"
          className="focus-visible:ring-ring rounded-full outline-none focus-visible:ring-2"
          aria-label="Menu utilisateur"
        >
          <Avatar className="size-9 border-2 border-primary/40">
            <AvatarFallback className="bg-primary font-semibold text-primary-foreground">
              {initials}
            </AvatarFallback>
          </Avatar>
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-52">
        <DropdownMenuLabel>{currentProfile.fullName}</DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem asChild>
          <Link href="/profile">
            <UserIcon className="mr-2 size-4" />
            Mon profil
          </Link>
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem className="text-brand-red focus:text-brand-red">
          <LogOut className="mr-2 size-4" />
          Se déconnecter
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
