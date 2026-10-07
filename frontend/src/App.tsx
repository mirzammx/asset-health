import { useState } from "react";
import { Search } from "lucide-react";
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { Input } from "@/components/ui/input";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AppSidebar } from "@/components/AppSidebar";
import { useHashRoute } from "@/hooks/useHashRoute";
import { AssetDetail } from "@/pages/AssetDetail";
import { Assets } from "@/pages/Assets";
import { Overview } from "@/pages/Overview";

export default function App() {
  const route = useHashRoute();
  const [query, setQuery] = useState("");
  const section = route[0] ?? "";

  const onSearch = (v: string) => {
    setQuery(v);
    if (section !== "assets" || route[1]) window.location.hash = "#/assets";
  };

  return (
    <TooltipProvider>
      <SidebarProvider>
        <AppSidebar active={section} />
        <SidebarInset>
          <header className="m-4 mb-0 flex items-center gap-3 rounded-xl border bg-card px-4 py-3">
            <SidebarTrigger />
            <div className="relative max-w-sm flex-1">
              <Search className="absolute left-2.5 top-2.5 size-4 text-muted-foreground" />
              <Input value={query} onChange={(e) => onSearch(e.target.value)} placeholder="Search assets…" className="border-0 bg-transparent pl-8" />
            </div>
          </header>
          <main className="p-4">
            {section === "assets" && route[1] ? <AssetDetail id={route[1]} key={route[1]} />
              : section === "assets" ? <Assets query={query} />
              : <Overview />}
          </main>
        </SidebarInset>
      </SidebarProvider>
    </TooltipProvider>
  );
}
