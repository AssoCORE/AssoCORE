import Link from "next/link";
import { AppSidebar } from "@/components/custom/sidebar";
import { SidebarProvider } from "@/components/ui/sidebar";

export default function Home() {
  return (
    <SidebarProvider>
      <div className="flex">
        <AppSidebar />
        <main className="flex-1">
          <h1>Page principale</h1>

          <Link href="/profile">
            <button>Aller à la page de profile</button>
          </Link>

          <Link href="/event">
            <button>Aller à la page d'evenement</button>
          </Link>

          <Link href="/calendar">
            <button>Aller à la page de calendrier</button>
          </Link>

          <Link href="/file">
            <button>Aller à la page de fichier</button>
          </Link>

          <Link href="/adminUser">
            <button>Aller à la page d'admin pour les profiles</button>
          </Link>

          <Link href="/adminEvent">
            <button>Aller à la page d'admin pour les events</button>
          </Link>
        </main>
      </div>
    </SidebarProvider>
  );
}