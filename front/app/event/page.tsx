import Link from "next/link";
import { AppSidebar } from "@/components/custom/sidebar";
import { SidebarProvider } from "@/components/ui/sidebar";
import Header from "@/components/custom/header";

export default function Home() {
  return (
    <SidebarProvider>
      <div className="flex">
        <AppSidebar />
        <Header />
        <main className="flex-1">
          <h1>Page Event</h1>
        </main>
      </div>
    </SidebarProvider>
  );
}
