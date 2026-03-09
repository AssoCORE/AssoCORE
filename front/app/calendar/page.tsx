import Link from "next/link";
import { AppSidebar } from "@/components/custom/sidebar";
import { SidebarProvider } from "@/components/ui/sidebar";
import Header from "@/components/custom/header";

export default function Home() {
  return (
    <SidebarProvider>
      <div className="flex">
        <AppSidebar />
        <main className="flex-1">
          <Header />
          <h1>Page Calendar</h1>
        </main>
      </div>
    </SidebarProvider>
  );
}
