"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart3, Cpu, Database, Layers, Search } from "lucide-react";
import { useAnalysis } from "@/components/AnalysisContext";

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: BarChart3 },
  { name: "Datasets", href: "/datasets", icon: Database },
  { name: "Trends & Topics", href: "/topics", icon: Layers },
  { name: "Explorer", href: "/explorer", icon: Search },
  { name: "Analysis", href: "/analysis", icon: Cpu },
];
export function Sidebar() {
  const pathname = usePathname(), ctx = useAnalysis();
  return <aside className="sidebar"><Link className="brand" href="/dashboard"><span className="brand-mark">STA</span><span>Social Trend Analyzer</span></Link>
    <nav aria-label="Primary navigation">{navigation.map(item => <Link key={item.href} href={`${item.href}${ctx.query ? `?${ctx.query}` : ""}`} aria-current={pathname.startsWith(item.href) ? "page" : undefined}><item.icon size={16} aria-hidden="true" />{item.name}</Link>)}</nav>
    <p className="sidebar-note">Dataset analysis on your machine.<br />Inspect the evidence behind each trend.</p>
  </aside>;
}
