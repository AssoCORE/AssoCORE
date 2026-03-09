"use client";

import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarTrigger,
} from "@/components/ui/sidebar";

import { useState } from "react";

import { Home, User, Settings, Mail, FileText } from "lucide-react";
import Link from "next/link";

type HeaderProps = {
  link: string;
  name: string;
};

export function AppSidebar() {
  const [search, setSearch] = useState("");
  const [administrator, setAdministrator] = useState(false);

  function SideBarHelper({ link, name }: HeaderProps) {
    return (
      <SidebarMenuItem>
        <SidebarMenuButton asChild>
          <Link href={link}>
            <Home />
            <span>{name}</span>
          </Link>
        </SidebarMenuButton>
      </SidebarMenuItem>
    );
  }

  return (
    <Sidebar collapsible="icon">
      <SidebarContent className="flex flex-col justify-center">
        {/* Search + checkbox admin */}
        <SidebarGroup>
          <div>
            <input
              type="text"
              placeholder="Rechercher... (NOT WORKING)"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <p>Texte recherché : {search}</p>
          </div>
        </SidebarGroup>

        {/* Public pages */}
        <SidebarGroup>
          <SidebarMenu>
            <SideBarHelper link="/" name="Acceuil" />
            <SideBarHelper link="/profile" name="Profile" />
            <SideBarHelper link="/event" name="Évènement" />
            <SideBarHelper link="/calendar" name="Calendrier" />
            <SideBarHelper link="/file" name="Dossiers" />
          </SidebarMenu>
        </SidebarGroup>

        {/* Admin pages */}
        {administrator && (
          <SidebarGroup>
            <SidebarGroupLabel>Administrateur</SidebarGroupLabel>

            <SidebarMenu>
              <SideBarHelper link="/adminUser" name="Adhérents" />
              <SideBarHelper link="/adminEvent" name="Gestion des évènements" />
            </SidebarMenu>
          </SidebarGroup>
        )}

        {/* BONUS*/}
        <SidebarGroup>
          {/* Checkbox pour activer admin */}
          <div>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={administrator}
                onChange={(e) => setAdministrator(e.target.checked)}
              />
              Mode administrateur
            </label>
          </div>
        </SidebarGroup>
      </SidebarContent>

      <SidebarTrigger />
    </Sidebar>
  );
}
