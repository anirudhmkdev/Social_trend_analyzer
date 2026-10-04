"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export function Header() {
  const [health, setHealth] = useState("Checking API…");
  async function check() { setHealth("Checking API…"); try { const result = await api.getHealth(); setHealth(result.status === "ok" ? "API available" : "API unavailable"); } catch { setHealth("API unavailable"); } }
  useEffect(() => { check(); }, []);
  return <header className="app-header"><span>Precision Intelligence Ledger</span><div><span role="status">{health}</span><button onClick={check} aria-label="Check API availability">Check again</button></div></header>;
}
