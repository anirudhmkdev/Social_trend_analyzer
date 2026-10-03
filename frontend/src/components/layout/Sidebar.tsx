"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  BarChart3,
  Cpu,
  Database,
  Layers,
  Search,
  Settings2,
} from "lucide-react";

interface NavItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
}

const navigation: NavItem[] = [
  { name: "Overview", href: "/", icon: Activity },
  { name: "Dashboard", href: "/dashboard", icon: BarChart3, badge: "Live" },
  { name: "Topics", href: "/topics", icon: Layers },
  { name: "Datasets", href: "/datasets", icon: Database },
  { name: "Search & Explorer", href: "/search", icon: Search },
  { name: "Pipeline Architecture", href: "/pipeline", icon: Cpu },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 border-r border-slate-200 bg-slate-50/80 flex flex-col justify-between h-screen sticky top-0 shrink-0">
      <div>
        {/* Brand */}
        <div className="h-16 flex items-center px-6 border-b border-slate-200 bg-white">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-sm bg-slate-900 flex items-center justify-center text-white font-semibold text-xs tracking-wider font-mono">
              STA
            </div>
            <div>
              <span className="font-semibold text-sm tracking-tight text-slate-900 block leading-tight font-sans">
                Social Trend
              </span>
              <span className="text-[10px] text-slate-500 font-mono tracking-wider uppercase">
                Intelligence Ledger
              </span>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="p-3 space-y-1">
          {navigation.map((item) => {
            const Icon = item.icon;
            const isCurrent =
              item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);

            return (
              <Link
                key={item.name}
                href={item.href}
                className={`flex items-center justify-between px-3 py-2 rounded-sm text-xs transition-colors ${
                  isCurrent
                    ? "bg-slate-900 text-white font-medium shadow-xs"
                    : "text-slate-600 hover:bg-slate-200/60 hover:text-slate-900"
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <Icon
                    className={`w-4 h-4 ${
                      isCurrent ? "text-sky-400" : "text-slate-500"
                    }`}
                  />
                  <span>{item.name}</span>
                </div>
                {item.badge && (
                  <span
                    className={`text-[9px] uppercase tracking-wider font-mono px-1.5 py-0.5 rounded-xs ${
                      isCurrent
                        ? "bg-slate-800 text-sky-300 border border-slate-700"
                        : "bg-slate-200/80 text-slate-600 border border-slate-300"
                    }`}
                  >
                    {item.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Footer System Status */}
      <div className="p-4 border-t border-slate-200 bg-white">
        <div className="flex items-center gap-2 mb-2.5">
          <Settings2 className="w-3.5 h-3.5 text-slate-400" />
          <span className="text-xs font-semibold text-slate-700 uppercase tracking-wider font-mono text-[10px]">
            System Status
          </span>
        </div>
        <div className="space-y-1.5 text-[11px] text-slate-600 font-mono">
          <div className="flex justify-between items-center">
            <span className="text-slate-500">Pipeline</span>
            <span className="inline-flex items-center gap-1.5 text-emerald-700 font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              Online
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">NLP Engine</span>
            <span className="text-slate-800">RoBERTa + MiniLM</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">Version</span>
            <span className="text-slate-800">1.0.0 (Canonical)</span>
          </div>
        </div>
      </div>
    </aside>
  );
}
