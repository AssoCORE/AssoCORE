"use client";

import type { ReactNode } from "react";

import { AppSidebar } from "@/components/custom/sidebar";
import { TopBar } from "@/components/custom/topbar";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import type { NotificationOut } from "@/lib/types";

export function AppShell({
  children,
  notifications,
  unreadCount,
}: {
  children: ReactNode;
  notifications: NotificationOut[];
  unreadCount: number;
}) {
  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset className="flex min-h-svh flex-col bg-background">
        <TopBar notifications={notifications} unreadCount={unreadCount} />
        <main className="flex flex-1 flex-col p-3 sm:p-4 md:p-6">
          {children}
        </main>
      </SidebarInset>
    </SidebarProvider>
  );
}
