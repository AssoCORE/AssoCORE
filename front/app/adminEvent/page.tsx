import Link from "next/link";
import { AppSidebar } from "@/components/custom/sidebar";
import { SidebarProvider } from "@/components/ui/sidebar";
import Header from "@/components/custom/header";

export default function Home() {
  return (
    <SidebarProvider>
      <div className="flex w-screen">
        <AppSidebar />
        <main className="flex flex-1 flex-col min-w-0">
          <Header />
          <h1>Page AdminEvent</h1>
        </main>
      </div>
    </SidebarProvider>
  );
}
