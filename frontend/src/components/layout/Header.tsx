"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { CheckCircle2, AlertCircle, RefreshCw } from "lucide-react";

export function Header() {
  const [healthStatus, setHealthStatus] = useState<"checking" | "online" | "offline">("checking");

  const checkHealth = async () => {
    setHealthStatus("checking");
    try {
      const res = await api.getHealth();
      if (res && res.status === "ok") {
        setHealthStatus("online");
      } else {
        setHealthStatus("offline");
      }
    } catch {
      setHealthStatus("offline");
    }
  };

  useEffect(() => {
    checkHealth();
  }, []);

  return (
    <header className="h-16 border-b border-zinc-200 bg-white px-8 flex items-center justify-between sticky top-0 z-10">
      <div className="flex items-center gap-3">
        <h1 className="text-sm font-semibold text-zinc-900 tracking-tight">
          System Overview
        </h1>
        <span className="text-zinc-300">/</span>
        <span className="text-xs text-zinc-500 font-normal">
          Phase 1 — Project Foundation
        </span>
      </div>

      <div className="flex items-center gap-4">
        {/* Backend API health badge */}
        <div className="flex items-center gap-2 px-2.5 py-1 bg-zinc-50 border border-zinc-200 rounded-md text-xs">
          <span className="text-zinc-500 font-mono text-[11px]">API:</span>
          {healthStatus === "online" && (
            <div className="flex items-center gap-1.5 text-emerald-700 font-medium">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              <span>Online (200 OK)</span>
            </div>
          )}
          {healthStatus === "offline" && (
            <div className="flex items-center gap-1.5 text-amber-700 font-medium">
              <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
              <span>Offline / Waiting</span>
            </div>
          )}
          {healthStatus === "checking" && (
            <div className="flex items-center gap-1.5 text-zinc-600">
              <RefreshCw className="w-3 h-3 animate-spin text-zinc-400" />
              <span>Checking...</span>
            </div>
          )}
          <button
            onClick={checkHealth}
            title="Recheck health"
            className="text-zinc-400 hover:text-zinc-600 p-0.5 ml-1 transition-colors"
          >
            <RefreshCw className="w-3 h-3" />
          </button>
        </div>

        <a
          href="https://github.com/anirudhmkdev/Social_trend_analyzer"
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs font-mono text-zinc-500 hover:text-zinc-900 transition-colors"
        >
          v0.1.0-alpha
        </a>
      </div>
    </header>
  );
}
