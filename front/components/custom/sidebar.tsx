"use client"

import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarTrigger,
} from "@/components/ui/sidebar"

import { useState } from "react"

import { Home, User, Settings, Mail, FileText } from "lucide-react"
import Link from "next/link"

export function AppSidebar() {
  const [search, setSearch] = useState("")
  const [administrator, setAdministrator] = useState(false)

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
            <SidebarMenuItem>
              <SidebarMenuButton asChild>
                <Link href="/">
                  <Home />
                  <span>Acceuil</span>
                </Link>
              </SidebarMenuButton>
            </SidebarMenuItem>

            <SidebarMenuItem>
              <SidebarMenuButton asChild>
                <Link href="/profile">
                  <User />
                  <span>Profile</span>
                </Link>
              </SidebarMenuButton>
            </SidebarMenuItem>

            <SidebarMenuItem>
              <SidebarMenuButton asChild>
                <Link href="/event">
                  <Mail />
                  <span>Évènement</span>
                </Link>
              </SidebarMenuButton>
            </SidebarMenuItem>

            <SidebarMenuItem>
              <SidebarMenuButton asChild>
                <Link href="/calendar">
                  <FileText />
                  <span>Calendrier</span>
                </Link>
              </SidebarMenuButton>
            </SidebarMenuItem>

            <SidebarMenuItem>
              <SidebarMenuButton asChild>
                <Link href="/file">
                  <Settings />
                  <span>Dossiers</span>
                </Link>
              </SidebarMenuButton>
            </SidebarMenuItem>

          </SidebarMenu>
        </SidebarGroup>

        {/* Admin pages */}
        {administrator && (
          <SidebarGroup>
            <SidebarGroupLabel>
              Administrateur
            </SidebarGroupLabel>

            <SidebarMenu>

              <SidebarMenuItem>
                <SidebarMenuButton asChild>
                  <Link href="/adminUser">
                    <User />
                    <span>Adhérents</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>

              <SidebarMenuItem>
                <SidebarMenuButton asChild>
                  <Link href="/adminEvent">
                    <Mail />
                    <span>Gestion des évènements</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>

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
  )
}