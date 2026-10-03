"use client";

import React, { useEffect, useState } from "react";
import {
  CheckCircle2,
  Clock,
  Loader2,
  Play,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import { api, DatasetItem } from "@/lib/api";

export default function DatasetsPage() {
  const [datasets, setDatasets] = useState<DatasetItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionInProgress, setActionInProgress] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const fetchDatasets = async () => {
    try {
      setLoading(true);
      const res = await api.getDatasets();
      setDatasets(res || []);
    } catch (err) {
      console.error("Failed to fetch datasets:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDatasets();
  }, []);

  const handleGenerateSample = async () => {
    try {
      setActionInProgress(true);
      setStatusMessage("Generating 850+ post synthetic dataset across 5 themes & 3 platforms...");
      const res = await api.loadSampleDataset();
      setStatusMessage(`Dataset created (${res.row_count} posts). Triggering NLP analysis pipeline...`);

      const runRes = await api.triggerAnalysisRun(res.dataset_id);
      const pollInterval = setInterval(async () => {
        try {
          const st = await api.getAnalysisRunStatus(runRes.id);
          setStatusMessage(`Pipeline executing: ${st.current_step} (${st.progress_pct}%)`);
          if (st.status === "completed") {
            clearInterval(pollInterval);
            setStatusMessage("Pipeline analysis completed successfully!");
            setTimeout(() => {
              setStatusMessage(null);
              setActionInProgress(false);
              fetchDatasets();
            }, 1000);
          } else if (st.status === "failed") {
            clearInterval(pollInterval);
            setStatusMessage(`Analysis failed: ${st.error_message || "Unknown error"}`);
            setActionInProgress(false);
          }
        } catch {
          clearInterval(pollInterval);
          setActionInProgress(false);
        }
      }, 1500);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error generating dataset";
      setStatusMessage(`Error: ${msg}`);
      setActionInProgress(false);
    }
  };

  const handleRunAnalysis = async (datasetId: string) => {
    try {
      setActionInProgress(true);
      setStatusMessage("Triggering analysis run on dataset...");
      const runRes = await api.triggerAnalysisRun(datasetId);

      const pollInterval = setInterval(async () => {
        try {
          const st = await api.getAnalysisRunStatus(runRes.id);
          setStatusMessage(`Pipeline executing: ${st.current_step} (${st.progress_pct}%)`);
          if (st.status === "completed") {
            clearInterval(pollInterval);
            setStatusMessage("Analysis completed successfully!");
            setTimeout(() => {
              setStatusMessage(null);
              setActionInProgress(false);
              fetchDatasets();
            }, 1000);
          } else if (st.status === "failed") {
            clearInterval(pollInterval);
            setStatusMessage(`Analysis failed: ${st.error_message || "Unknown error"}`);
            setActionInProgress(false);
          }
        } catch {
          clearInterval(pollInterval);
          setActionInProgress(false);
        }
      }, 1500);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error running analysis";
      setStatusMessage(`Error: ${msg}`);
      setActionInProgress(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900 font-sans">
            Dataset Repository & Ingestion
          </h1>
          <p className="text-xs text-slate-500 mt-1 font-sans">
            Manage ingested social corpora, canonical immutable preprocessed texts, and triggered analysis runs.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={fetchDatasets}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xs border border-slate-200 bg-white text-xs font-medium text-slate-700 hover:bg-slate-50 transition-colors shadow-2xs cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>

          <button
            onClick={handleGenerateSample}
            disabled={actionInProgress}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xs bg-slate-900 text-white text-xs font-medium hover:bg-slate-800 transition-colors shadow-xs cursor-pointer font-sans"
          >
            {actionInProgress ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Sparkles className="w-3.5 h-3.5" />
            )}
            Load 850-Post Demo Dataset
          </button>
        </div>
      </div>

      {/* Progress banner */}
      {statusMessage && (
        <div className="p-3 bg-sky-50 border border-sky-200 text-sky-900 rounded-xs text-xs font-mono flex items-center gap-2">
          <Loader2 className="w-4 h-4 animate-spin text-sky-600 shrink-0" />
          <span>{statusMessage}</span>
        </div>
      )}

      {/* Dataset Table Ledger */}
      <div className="bg-white border border-slate-200 rounded-xs shadow-2xs overflow-hidden">
        <div className="p-4 border-b border-slate-200 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-900 font-sans">
            Ingested Corpora Ledger
          </h2>
          <span className="text-xs font-mono text-slate-400">
            {datasets.length} Total Datasets
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 font-mono text-[11px] text-slate-500 uppercase tracking-wider">
                <th className="py-2.5 px-4">Dataset Name</th>
                <th className="py-2.5 px-4">Source Type</th>
                <th className="py-2.5 px-4 font-mono-numbers">Post Count</th>
                <th className="py-2.5 px-4">Ingestion Date</th>
                <th className="py-2.5 px-4">Pipeline Status</th>
                <th className="py-2.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-sans">
              {loading ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-500 font-mono text-xs">
                    <Loader2 className="w-4 h-4 animate-spin inline-block mr-2" />
                    Loading Datasets...
                  </td>
                </tr>
              ) : datasets.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-400 font-mono text-xs">
                    No datasets loaded yet. Click &quot;Load 850-Post Demo Dataset&quot; to begin.
                  </td>
                </tr>
              ) : (
                datasets.map((ds) => (
                  <tr key={ds.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-3 px-4">
                      <div className="font-semibold text-slate-900">{ds.name}</div>
                      <div className="text-[10px] font-mono text-slate-400">{ds.filename}</div>
                    </td>
                    <td className="py-3 px-4 font-mono uppercase text-[11px] text-slate-600">
                      {ds.source_type}
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-800 font-semibold">
                      {(ds.valid_row_count || ds.row_count || 0).toLocaleString()}
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-500 text-[11px]">
                      {new Date(ds.created_at).toLocaleDateString("en-US", {
                        month: "short",
                        day: "numeric",
                        year: "numeric",
                      })}
                    </td>
                    <td className="py-3 px-4">
                      {ds.latest_run?.status === "completed" ? (
                        <span className="inline-flex items-center gap-1 text-emerald-700 font-mono text-[11px] font-medium">
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                          Analyzed
                        </span>
                      ) : ds.latest_run?.status === "running" ? (
                        <span className="inline-flex items-center gap-1 text-sky-700 font-mono text-[11px] font-medium">
                          <Loader2 className="w-3.5 h-3.5 animate-spin text-sky-600" />
                          Running
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-slate-500 font-mono text-[11px]">
                          <Clock className="w-3.5 h-3.5" />
                          Pending Analysis
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => handleRunAnalysis(ds.id)}
                        disabled={actionInProgress}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-xs bg-slate-900 text-white text-[11px] font-mono hover:bg-slate-800 transition-colors disabled:opacity-50 cursor-pointer"
                      >
                        <Play className="w-3 h-3 fill-current" />
                        Run Pipeline
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
