import { Activity, LayoutDashboard, Server } from "lucide-react";
import {
  Sidebar, SidebarContent, SidebarGroup, SidebarGroupContent, SidebarGroupLabel, SidebarHeader,
  SidebarMenu, SidebarMenuButton, SidebarMenuItem,
} from "@/components/ui/sidebar";

const NAV = [
  { key: "", label: "Overview", href: "#/", icon: LayoutDashboard },
  { key: "assets", label: "Assets", href: "#/assets", icon: Server },
];

export function AppSidebar({ active }: { active: string }) {
  return (
    <Sidebar collapsible="icon">
      <SidebarHeader>
        <div className="flex items-center gap-3 px-1 py-1">
          <div className="flex size-9 shrink-0 items-center justify-center rounded-full bg-foreground text-background">
            <Activity className="size-5" />
          </div>
          <div className="leading-tight group-data-[collapsible=icon]:hidden">
            <div className="font-semibold">Asset Health</div>
            <div className="text-xs text-muted-foreground">Predictive maintenance</div>
          </div>
        </div>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Monitoring</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {NAV.map(({ key, label, href, icon: Icon }) => (
                <SidebarMenuItem key={key}>
                  <SidebarMenuButton isActive={active === key} tooltip={label} render={<a href={href} />}>
                    <Icon />
                    <span>{label}</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
}
