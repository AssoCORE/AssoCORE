"use client";

import type { ReactNode } from "react";

import { AdminProvider } from "@/components/custom/admin-provider";
import { AppSidebar } from "@/components/custom/sidebar";
import { TopBar } from "@/components/custom/topbar";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <AdminProvider>
      <SidebarProvider>
        <AppSidebar />
        <SidebarInset className="flex min-h-svh flex-col bg-background">
          <TopBar />
          <main className="flex flex-1 flex-col p-3 sm:p-4 md:p-6">
            {children}
          </main>
        </SidebarInset>
      </SidebarProvider>
    </AdminProvider>
  );
}
