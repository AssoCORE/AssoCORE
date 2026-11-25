"use client";

import { format } from "date-fns";
import { fr } from "date-fns/locale";
import {
  Bell,
  CheckCheck,
  LogOut,
  Mail,
  Moon,
  Sun,
  Trash2,
  User as UserIcon,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTheme } from "next-themes";
import { Fragment, useSyncExternalStore, useTransition } from "react";
import { useAuth } from "@/components/auth/AuthProvider";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useLogout } from "@/hooks/use-logout";
import {
  deleteNotification,
  markAllNotificationsRead,
  markNotificationRead,
  markNotificationUnread,
} from "@/lib/actions";
import { parseServerDate } from "@/lib/format";
import { fullName, initialsOf, labelOf } from "@/lib/roles";
import type { NotificationOut } from "@/lib/types";
import { cn } from "@/lib/utils";

const ROOT_LABEL = "AssoName";

const segmentLabel: Record<string, string> = {
  event: "Évènements",
  calendar: "Calendrier",
  file: "Dossiers",
  profile: "Profil",
  adminUser: "Gestionnaire d'Adhérent",
  adminEvent: "Gestionnaire Dossier",
  budget: "Budget",
};

function humanize(segment: string) {
  // Ids (/event/12, /adminUser/3) read as a detail page, not as a number.
  if (/^\d+$/.test(segment)) return "Détail";
  return segmentLabel[segment] ?? segment.replace(/-/g, " ");
}

export function TopBar({
  notifications,
  unreadCount,
}: {
  notifications: NotificationOut[];
  unreadCount: number;
}) {
  const pathname = usePathname();
  const segments = pathname.split("/").filter(Boolean);
  const trail = segments.map((seg, idx) => ({
    label: humanize(seg),
    href: `/${segments.slice(0, idx + 1).join("/")}`,
  }));

  return (
    <header className="sticky top-0 z-10 flex h-14 items-center justify-between gap-2 border-b border-border bg-card px-4 md:px-6">
      <div className="flex min-w-0 items-center gap-2">
        <Breadcrumb className="min-w-0">
          <BreadcrumbList className="flex-nowrap text-sm">
            <BreadcrumbItem className="hidden sm:inline-flex">
              <BreadcrumbLink asChild>
                <Link
                  href="/"
                  className="font-medium underline underline-offset-4"
                >
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
        <NotificationsMenu
          notifications={notifications}
          unreadCount={unreadCount}
        />
        <UserMenu />
      </div>
    </header>
  );
}

const noopSubscribe = () => () => {};

function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  // false during SSR and hydration, true afterwards: the theme is only known on
  // the client, so rendering it earlier would cause a hydration mismatch.
  const mounted = useSyncExternalStore(
    noopSubscribe,
    () => true,
    () => false
  );
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

function NotificationsMenu({
  notifications,
  unreadCount,
}: {
  notifications: NotificationOut[];
  unreadCount: number;
}) {
  const [pending, startTransition] = useTransition();
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="relative"
          aria-label={`Notifications (${unreadCount} non lues)`}
        >
          <Bell className="size-5" />
          {unreadCount > 0 && (
            <span className="absolute right-1 top-1 flex min-w-4 items-center justify-center rounded-full bg-brand-red px-1 text-[10px] font-semibold leading-4 text-white">
              {unreadCount > 9 ? "9+" : unreadCount}
            </span>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-80">
        <div className="flex items-center justify-between px-2 py-1.5">
          <DropdownMenuLabel className="p-0">Notifications</DropdownMenuLabel>
          {unreadCount > 0 && (
            <Button
              variant="ghost"
              size="xs"
              disabled={pending}
              onClick={() =>
                startTransition(
                  async () => void (await markAllNotificationsRead())
                )
              }
            >
              <CheckCheck />
              Tout marquer lu
            </Button>
          )}
        </div>
        <DropdownMenuSeparator />
        {notifications.length === 0 ? (
          <p className="px-2 py-4 text-center text-sm text-muted-foreground">
            Aucune notification.
          </p>
        ) : (
          notifications.map((n) => (
            <DropdownMenuItem
              key={n.id}
              className="group/notif flex items-start gap-2"
              onSelect={() => {
                if (!n.read)
                  startTransition(
                    async () => void (await markNotificationRead(n.id))
                  );
              }}
            >
              <div className="flex min-w-0 flex-1 flex-col items-start gap-0.5">
                <span className={cn("text-sm", !n.read && "font-semibold")}>
                  {n.message}
                </span>
                <span className="text-xs text-muted-foreground">
                  {format(parseServerDate(n.date), "d MMM yyyy · HH:mm", {
                    locale: fr,
                  })}
                </span>
              </div>
              {/* Revealed on hover/focus; stopPropagation keeps the item's own onSelect out of it. */}
              <div className="flex shrink-0 gap-0.5 opacity-0 transition group-hover/notif:opacity-100 group-focus/notif:opacity-100 pointer-coarse:opacity-100">
                {n.read && (
                  <Button
                    variant="ghost"
                    size="icon-sm"
                    aria-label="Marquer non lue"
                    disabled={pending}
                    onClick={(e) => {
                      e.stopPropagation();
                      e.preventDefault();
                      startTransition(
                        async () => void (await markNotificationUnread(n.id))
                      );
                    }}
                  >
                    <Mail className="size-3.5" />
                  </Button>
                )}
                <Button
                  variant="ghost"
                  size="icon-sm"
                  aria-label="Supprimer la notification"
                  disabled={pending}
                  onClick={(e) => {
                    e.stopPropagation();
                    e.preventDefault();
                    startTransition(
                      async () => void (await deleteNotification(n.id))
                    );
                  }}
                >
                  <Trash2 className="size-3.5" />
                </Button>
              </div>
            </DropdownMenuItem>
          ))
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

function UserMenu() {
  const user = useAuth();
  const logout = useLogout();
  const initials = initialsOf(user.firstname, user.name);
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
        <DropdownMenuLabel className="flex flex-col">
          <span>{fullName(user)}</span>
          <span className="text-xs font-normal text-muted-foreground">
            {user.roles.map(labelOf).join(", ") || "Aucun rôle"}
          </span>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem asChild>
          <Link href="/profile">
            <UserIcon className="mr-2 size-4" />
            Mon profil
          </Link>
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem
          className="text-brand-red focus:text-brand-red"
          onSelect={() => void logout()}
        >
          <LogOut className="mr-2 size-4" />
          Se déconnecter
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
