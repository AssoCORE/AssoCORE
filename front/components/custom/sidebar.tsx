"use client";

import {
  Calendar,
  ChevronDown,
  FileText,
  Folder,
  LayoutGrid,
  LogOut,
  Search,
  Users,
  Wallet,
  User as UserIcon,
  ImageIcon,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ComponentType } from "react";

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarTrigger,
  useSidebar,
} from "@/components/ui/sidebar";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/components/auth/AuthProvider";
import { useLogout } from "@/hooks/use-logout";
import { isAdmin as hasAdminRole } from "@/lib/auth/roles";
import { labelOf } from "@/lib/roles";
import { cn } from "@/lib/utils";

type NavItem = {
  label: string;
  href: string;
  icon: ComponentType<{ className?: string }>;
};

const publicItems: NavItem[] = [
  { label: "Accueil", href: "/", icon: LayoutGrid },
  { label: "Évènements", href: "/event", icon: Calendar },
  { label: "Dossiers", href: "/file", icon: FileText },
  { label: "Profile", href: "/profile", icon: UserIcon },
];

const adminItems: NavItem[] = [
  { label: "Gestion d'Adhérents", href: "/adminUser", icon: Users },
  { label: "Gestionnaire Dossier", href: "/adminEvent", icon: Folder },
  { label: "Budget", href: "/budget", icon: Wallet },
];

export function AppSidebar() {
  const { state } = useSidebar();
  const user = useAuth();
  const logout = useLogout();
  // UX only — the backend's require_admin enforces it on every admin call.
  const isAdmin = hasAdminRole(user);
  const collapsed = state === "collapsed";

  return (
    <Sidebar collapsible="icon" className="border-r-0">
      <SidebarHeader className="gap-3 p-3">
        <div className="flex items-center gap-2">
          <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-white/10">
            <ImageIcon className="size-5 text-white/80" />
          </div>
          {!collapsed && (
            <div className="flex min-w-0 flex-col">
              <span className="truncate text-sm font-semibold text-sidebar-foreground">
                AssoName
              </span>
              <span className="flex items-center gap-1 text-xs text-sidebar-foreground/60">
                <UserIcon className="size-3" />
                {user.roles.map(labelOf).join(", ") || "Aucun rôle"}
              </span>
            </div>
          )}
        </div>

        {collapsed ? (
          <button
            type="button"
            className="mx-auto flex size-8 items-center justify-center rounded-md bg-white/10 text-white/70 transition hover:bg-white/15"
            aria-label="Rechercher"
          >
            <Search className="size-4" />
          </button>
        ) : (
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-sidebar-foreground/50" />
            <Input
              placeholder="Recherche (Ctrl+/)"
              className="h-9 border-white/10 bg-white/5 pl-8 text-sidebar-foreground placeholder:text-sidebar-foreground/50 focus-visible:ring-white/20"
            />
          </div>
        )}
      </SidebarHeader>

      <div className="relative">
        <SidebarTrigger
          className={cn(
            "absolute -right-3 top-1 z-20 size-6 rounded-full border border-white/10 bg-white text-slate-800 shadow hover:bg-white",
          )}
        />
      </div>

      <SidebarContent className="gap-1 px-2">
        <NavSection title="Public" items={publicItems} collapsed={collapsed} />
        {isAdmin && (
          <NavSection title="Admin" items={adminItems} collapsed={collapsed} />
        )}
      </SidebarContent>

      <SidebarFooter className="gap-3 p-3">
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              asChild
              tooltip="Se déconnecter"
              className="text-brand-red hover:bg-white/5 hover:text-brand-red"
            >
              <button type="button" aria-label="Se déconnecter" onClick={() => void logout()}>
                <LogOut />
                {!collapsed && <span>Se déconnecter</span>}
              </button>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  );
}

function NavSection({
  title,
  items,
  collapsed,
}: {
  title: string;
  items: NavItem[];
  collapsed: boolean;
}) {
  const pathname = usePathname();

  if (collapsed) {
    return (
      <SidebarGroup className="p-0">
        <SidebarMenu>
          {items.map((item) => (
            <NavItemRow key={item.href} item={item} pathname={pathname} />
          ))}
        </SidebarMenu>
      </SidebarGroup>
    );
  }

  return (
    <Collapsible defaultOpen className="group/section">
      <SidebarGroup className="p-0">
        <CollapsibleTrigger asChild>
          <button
            type="button"
            className="flex w-full items-center justify-between rounded-md px-3 py-2 text-xs font-medium uppercase tracking-wide text-sidebar-foreground/60 transition hover:text-sidebar-foreground"
          >
            {title}
            <ChevronDown className="size-3 transition-transform group-data-[state=closed]/section:-rotate-90" />
          </button>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <SidebarMenu>
            {items.map((item) => (
              <NavItemRow key={item.href} item={item} pathname={pathname} />
            ))}
          </SidebarMenu>
        </CollapsibleContent>
      </SidebarGroup>
    </Collapsible>
  );
}

function NavItemRow({
  item,
  pathname,
}: {
  item: NavItem;
  pathname: string;
}) {
  const active = pathname === item.href;
  return (
    <SidebarMenuItem>
      <SidebarMenuButton
        asChild
        isActive={active}
        tooltip={item.label}
        className={cn(
          "relative text-sidebar-foreground/80 hover:bg-white/5 hover:text-sidebar-foreground",
          active &&
            "bg-transparent text-primary hover:bg-white/5 hover:text-primary data-[active=true]:bg-transparent data-[active=true]:text-primary",
        )}
      >
        <Link href={item.href}>
          <item.icon />
          <span>{item.label}</span>
          {active && (
            <span className="absolute inset-y-1 right-0 w-1 rounded-l bg-primary" />
          )}
        </Link>
      </SidebarMenuButton>
    </SidebarMenuItem>
  );
}

