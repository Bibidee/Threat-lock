import type { ReactNode } from "react";

import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar />
        <main className="mx-auto w-full max-w-7xl flex-1 space-y-6 px-4 py-6 sm:px-6 lg:px-8">
          {children}
        </main>
        <footer className="border-t border-border px-6 py-4 text-center text-[0.7rem] uppercase tracking-[0.14em] text-muted">
          Threat-Lock · AI-native emergency response on GenLayer StudioNet
        </footer>
      </div>
    </div>
  );
}
