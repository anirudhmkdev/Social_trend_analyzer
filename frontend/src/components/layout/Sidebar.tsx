import React from "react";
import Link from "next/link";
import {
  Activity,
  BarChart3,
  Database,
  Layers,
  Search,
  Settings2,
} from "lucide-react";

interface NavItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  status?: string;
}

const navigation: NavItem[] = [
  { name: "Overview", href: "/", icon: Activity },
  { name: "Dashboard", href: "#", icon: BarChart3, status: "Phase 9" },
  { name: "Topics", href: "#", icon: Layers, status: "Phase 5" },
  { name: "Datasets", href: "#", icon: Database, status: "Phase 2" },
  { name: "Search & Filter", href: "#", icon: Search, status: "Phase 8" },
];

export function Sidebar() {
  return (
    <aside className="w-64 border-r border-zinc-200 bg-zinc-50 flex flex-col justify-between h-screen sticky top-0">
      <div>
        {/* Brand */}
        <div className="h-16 flex items-center px-6 border-b border-zinc-200">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-md bg-zinc-900 flex items-center justify-center text-white font-semibold text-xs tracking-wider">
              STA
            </div>
            <div>
              <span className="font-semibold text-sm tracking-tight text-zinc-900 block leading-tight">
                Social Trend
              </span>
              <span className="text-[11px] text-zinc-500 font-medium tracking-wide uppercase">
                Analyzer
              </span>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="p-3 space-y-1">
          {navigation.map((item) => {
            const Icon = item.icon;
            const isCurrent = item.href === "/";
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`flex items-center justify-between px-3 py-2 rounded-md text-xs font-medium transition-colors ${
                  isCurrent
                    ? "bg-zinc-200/70 text-zinc-900 font-semibold"
                    : "text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900"
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <Icon className="w-4 h-4 text-zinc-500" />
                  <span>{item.name}</span>
                </div>
                {item.status && (
                  <span className="text-[10px] uppercase tracking-wider font-mono text-zinc-400 border border-zinc-200 px-1.5 py-0.5 rounded">
                    {item.status}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Footer Info */}
      <div className="p-4 border-t border-zinc-200 bg-zinc-50/50">
        <div className="flex items-center gap-2 mb-2">
          <Settings2 className="w-3.5 h-3.5 text-zinc-400" />
          <span className="text-xs font-medium text-zinc-600">Environment</span>
        </div>
        <div className="space-y-1 text-[11px] text-zinc-500">
          <div className="flex justify-between">
            <span>Status</span>
            <span className="font-mono text-emerald-600 font-semibold">Phase 1</span>
          </div>
          <div className="flex justify-between">
            <span>Backend</span>
            <span className="font-mono">FastAPI</span>
          </div>
          <div className="flex justify-between">
            <span>Frontend</span>
            <span className="font-mono">Next.js 15</span>
          </div>
        </div>
      </div>
    </aside>
  );
}
