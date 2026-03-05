import Link from "next/link";
import { AppSidebar } from "@/components/custom/sidebar";
import { SidebarProvider } from "@/components/ui/sidebar";

export default function Home() {
  return (
    <SidebarProvider>
      <div className="flex">
        <AppSidebar />
        <main className="flex-1">
          <h1>Page File</h1>

        </main>
      </div>
    </SidebarProvider>
  );
}
