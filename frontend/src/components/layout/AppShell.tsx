import React, { Suspense } from "react";
import { AnalysisProvider } from "@/components/AnalysisContext";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";

interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  return (
    <Suspense fallback={<p role="status">Loading workbench…</p>}><AnalysisProvider><div className="app-shell">
      <a href="#main-content" className="skip-link">Skip to content</a>
      <Sidebar />
      <div className="workspace">
        <Header />
        <main id="main-content" className="page">
          {children}
        </main>
      </div>
    </div></AnalysisProvider></Suspense>
  );
}
