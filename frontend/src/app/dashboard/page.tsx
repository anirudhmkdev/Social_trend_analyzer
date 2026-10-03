"use client";

import React, { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowDownRight,
  ArrowUpRight,
  BarChart2,
  Database,
  Flame,
  Hash,
  Layers,
  Loader2,
  MessageSquare,
  Play,
  RefreshCw,
  Sparkles,
  TrendingUp,
  Users,
} from "lucide-react";
import {
  api,
  DashboardSummary,
  TimelinePoint,
  TrendSnapshot,
} from "@/lib/api";

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [timeline, setTimeline] = useState<TimelinePoint[]>([]);
  const [timeWindow, setTimeWindow] = useState<"hourly" | "daily" | "weekly">("daily");
  const [loading, setLoading] = useState(true);
  const [runningAction, setRunningAction] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const sum = await api.getDashboardSummary();
      setSummary(sum);

      if (sum.analysis_run_id) {
        const tl = await api.getTimeline(sum.analysis_run_id, undefined, timeWindow);
        setTimeline(tl.timeline || []);
      } else {
        setTimeline([]);
      }
    } catch (err) {
      console.error("Failed to load dashboard summary:", err);
    } finally {
      setLoading(false);
    }
  }, [timeWindow]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleLoadSample = async () => {
    try {
      setRunningAction(true);
      setStatusMessage("Generating 850+ post synthetic dataset across 5 themes...");
      const res = await api.loadSampleDataset();
      setStatusMessage(`Dataset created (${res.row_count} posts). Triggering NLP analysis pipeline...`);
      const runRes = await api.triggerAnalysisRun(res.dataset_id);
      
      // Poll run status
      const pollInterval = setInterval(async () => {
        try {
          const st = await api.getAnalysisRunStatus(runRes.id);
          setStatusMessage(`Analyzing: ${st.current_step} (${st.progress_pct}%)`);
          if (st.status === "completed") {
            clearInterval(pollInterval);
            setStatusMessage("Analysis completed successfully!");
            setTimeout(() => {
              setStatusMessage(null);
              setRunningAction(false);
              loadData();
            }, 1000);
          } else if (st.status === "failed") {
            clearInterval(pollInterval);
            setStatusMessage(`Run failed: ${st.error_message || "Unknown error"}`);
            setRunningAction(false);
          }
        } catch {
          clearInterval(pollInterval);
          setRunningAction(false);
        }
      }, 1500);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load sample dataset";
      setStatusMessage(`Error: ${msg}`);
      setRunningAction(false);
    }
  };

  const getClassificationBadge = (classification: TrendSnapshot["classification"]) => {
    switch (classification) {
      case "emerging":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-xs text-[11px] font-mono font-medium bg-amber-50 text-amber-800 border border-amber-200">
            <Flame className="w-3 h-3 text-amber-600" />
            Emerging
          </span>
        );
      case "rising":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-xs text-[11px] font-mono font-medium bg-teal-50 text-teal-800 border border-teal-200">
            <ArrowUpRight className="w-3 h-3 text-teal-600" />
            Rising
          </span>
        );
      case "declining":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-xs text-[11px] font-mono font-medium bg-rose-50 text-rose-800 border border-rose-200">
            <ArrowDownRight className="w-3 h-3 text-rose-600" />
            Declining
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-xs text-[11px] font-mono font-medium bg-slate-100 text-slate-700 border border-slate-200">
            Stable
          </span>
        );
    }
  };

  if (loading && !summary) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-3 text-slate-500">
        <Loader2 className="w-6 h-6 animate-spin text-slate-700" />
        <span className="font-mono text-xs tracking-wider uppercase">Loading Intelligence Ledger...</span>
      </div>
    );
  }

  const hasData = summary && summary.status !== "no_data" && summary.total_posts > 0;

  return (
    <div className="space-y-6">
      {/* Top Ledger Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold tracking-tight text-slate-900 font-sans">
              Trend Intelligence Dashboard
            </h1>
            <span className="font-mono text-[10px] px-1.5 py-0.5 rounded-xs bg-slate-200 text-slate-700 uppercase tracking-wider">
              {summary?.dataset_name || "Live Ledger"}
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1 font-sans">
            Continuous NLP monitoring across thematic topic clusters, sentiment dynamics, and burst velocity.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          {/* Window Filter */}
          <div className="inline-flex rounded-xs border border-slate-200 bg-white p-0.5 shadow-2xs font-mono text-xs">
            {(["hourly", "daily", "weekly"] as const).map((w) => (
              <button
                key={w}
                onClick={() => setTimeWindow(w)}
                className={`px-2.5 py-1 rounded-xs transition-colors capitalize ${
                  timeWindow === w
                    ? "bg-slate-900 text-white font-medium"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                {w}
              </button>
            ))}
          </div>

          <button
            onClick={loadData}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xs border border-slate-200 bg-white text-xs font-medium text-slate-700 hover:bg-slate-50 transition-colors shadow-2xs cursor-pointer"
            title="Refresh Ledger"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>

          {!hasData && (
            <button
              onClick={handleLoadSample}
              disabled={runningAction}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xs bg-slate-900 text-white text-xs font-medium hover:bg-slate-800 transition-colors shadow-xs cursor-pointer"
            >
              {runningAction ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Play className="w-3.5 h-3.5 fill-current" />
              )}
              Load Demo Dataset
            </button>
          )}
        </div>
      </div>

      {/* Status banner if action running */}
      {statusMessage && (
        <div className="p-3 bg-sky-50 border border-sky-200 text-sky-900 rounded-xs text-xs font-mono flex items-center gap-2">
          <Loader2 className="w-4 h-4 animate-spin text-sky-600 shrink-0" />
          <span>{statusMessage}</span>
        </div>
      )}

      {!hasData ? (
        /* Empty State */
        <div className="border border-dashed border-slate-300 rounded-xs p-12 text-center bg-white space-y-4">
          <div className="w-12 h-12 rounded-sm bg-slate-100 flex items-center justify-center mx-auto text-slate-600">
            <Database className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-slate-900 font-sans">No Active Analysis Data</h3>
            <p className="text-xs text-slate-500 max-w-md mx-auto mt-1 font-sans">
              There is currently no completed analysis run in the database. Load the pre-configured multi-theme synthetic dataset (850+ posts) or upload a CSV file to inspect live NLP trends.
            </p>
          </div>
          <button
            onClick={handleLoadSample}
            disabled={runningAction}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xs bg-slate-900 text-white text-xs font-medium hover:bg-slate-800 transition-colors shadow-xs cursor-pointer font-sans"
          >
            {runningAction ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
            Generate & Analyze Demo Dataset
          </button>
        </div>
      ) : (
        <>
          {/* KPI Ledger Metric Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {/* Total Ingested Posts */}
            <div className="bg-white border border-slate-200 rounded-xs p-4 shadow-2xs">
              <div className="flex items-center justify-between text-slate-500 text-xs font-mono uppercase tracking-wider">
                <span>Total Posts</span>
                <MessageSquare className="w-4 h-4 text-slate-400" />
              </div>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-semibold text-slate-900 font-mono tracking-tight">
                  {summary.total_posts.toLocaleString()}
                </span>
                <span className="text-[11px] text-slate-500 font-mono">records</span>
              </div>
              <div className="mt-2 pt-2 border-t border-slate-100 flex gap-1.5 flex-wrap">
                {Object.entries(summary.platform_breakdown).map(([plat, count]) => (
                  <span
                    key={plat}
                    className="text-[10px] font-mono px-1.5 py-0.5 rounded-xs bg-slate-100 text-slate-600 uppercase"
                  >
                    {plat}: {count}
                  </span>
                ))}
              </div>
            </div>

            {/* Topics Discovered */}
            <div className="bg-white border border-slate-200 rounded-xs p-4 shadow-2xs">
              <div className="flex items-center justify-between text-slate-500 text-xs font-mono uppercase tracking-wider">
                <span>Discovered Topics</span>
                <Layers className="w-4 h-4 text-slate-400" />
              </div>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-semibold text-slate-900 font-mono tracking-tight">
                  {summary.total_topics}
                </span>
                <span className="text-[11px] text-slate-500 font-mono">clusters</span>
              </div>
              <div className="mt-2 pt-2 border-t border-slate-100 text-[11px] text-slate-500 font-mono">
                BERTopic + HDBSCAN + c-TF-IDF
              </div>
            </div>

            {/* Trend Momentum Breakdown */}
            <div className="bg-white border border-slate-200 rounded-xs p-4 shadow-2xs">
              <div className="flex items-center justify-between text-slate-500 text-xs font-mono uppercase tracking-wider">
                <span>Trend Dynamics</span>
                <TrendingUp className="w-4 h-4 text-teal-600" />
              </div>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-semibold text-teal-700 font-mono tracking-tight">
                  {(summary.trend_classifications.emerging || 0) + (summary.trend_classifications.rising || 0)}
                </span>
                <span className="text-[11px] text-slate-500 font-mono">active surge</span>
              </div>
              <div className="mt-2 pt-2 border-t border-slate-100 flex justify-between text-[11px] font-mono">
                <span className="text-amber-700 font-medium">
                  {summary.trend_classifications.emerging || 0} Emerging
                </span>
                <span className="text-teal-700 font-medium">
                  {summary.trend_classifications.rising || 0} Rising
                </span>
                <span className="text-slate-600">
                  {summary.trend_classifications.stable || 0} Stable
                </span>
              </div>
            </div>

            {/* Sentiment Balance */}
            <div className="bg-white border border-slate-200 rounded-xs p-4 shadow-2xs">
              <div className="flex items-center justify-between text-slate-500 text-xs font-mono uppercase tracking-wider">
                <span>Sentiment Balance</span>
                <span className="w-2 h-2 rounded-full bg-emerald-500" />
              </div>
              <div className="mt-2 flex items-baseline gap-2 font-mono">
                <span className="text-2xl font-semibold text-emerald-700">
                  {summary.sentiment_breakdown.percentages.positive || 0}%
                </span>
                <span className="text-[11px] text-slate-500">positive</span>
              </div>
              <div className="mt-2 pt-2 border-t border-slate-100">
                <div className="w-full h-1.5 bg-slate-100 rounded-xs flex overflow-hidden">
                  <div
                    style={{ width: `${summary.sentiment_breakdown.percentages.positive || 0}%` }}
                    className="bg-emerald-500"
                    title={`Positive: ${summary.sentiment_breakdown.counts.positive}`}
                  />
                  <div
                    style={{ width: `${summary.sentiment_breakdown.percentages.neutral || 0}%` }}
                    className="bg-slate-400"
                    title={`Neutral: ${summary.sentiment_breakdown.counts.neutral}`}
                  />
                  <div
                    style={{ width: `${summary.sentiment_breakdown.percentages.negative || 0}%` }}
                    className="bg-rose-500"
                    title={`Negative: ${summary.sentiment_breakdown.counts.negative}`}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Temporal Trajectory Ledger (Activity Timeline) */}
          <div className="bg-white border border-slate-200 rounded-xs p-5 shadow-2xs space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-sm font-semibold text-slate-900 font-sans">
                  Temporal Volume & Sentiment Spectrum
                </h2>
                <p className="text-[11px] text-slate-500 font-sans">
                  Strictly aligned to UTC calendar boundaries ({timeWindow}).
                </p>
              </div>
              <div className="flex items-center gap-3 text-xs font-mono text-slate-600">
                <span className="flex items-center gap-1">
                  <span className="w-2.5 h-2.5 rounded-xs bg-emerald-500" /> Pos
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-2.5 h-2.5 rounded-xs bg-slate-400" /> Neu
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-2.5 h-2.5 rounded-xs bg-rose-500" /> Neg
                </span>
              </div>
            </div>

            {/* Timeline Visual Bars */}
            {timeline.length === 0 ? (
              <div className="py-8 text-center text-xs text-slate-400 font-mono">
                No timeline points recorded for selected window.
              </div>
            ) : (
              <div className="pt-2">
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 lg:grid-cols-8 gap-2">
                  {timeline.map((pt, idx) => {
                    const dateStr = new Date(pt.window_start).toLocaleDateString("en-US", {
                      month: "short",
                      day: "numeric",
                    });
                    const posPct = pt.total_volume > 0 ? (pt.positive_count / pt.total_volume) * 100 : 0;
                    const neuPct = pt.total_volume > 0 ? (pt.neutral_count / pt.total_volume) * 100 : 0;
                    const negPct = pt.total_volume > 0 ? (pt.negative_count / pt.total_volume) * 100 : 0;

                    return (
                      <div
                        key={idx}
                        className="border border-slate-200 rounded-xs p-2.5 bg-slate-50/50 hover:bg-white hover:border-slate-300 transition-colors flex flex-col justify-between"
                      >
                        <div className="flex items-center justify-between text-[11px] font-mono text-slate-500">
                          <span>{dateStr}</span>
                          <span className="font-semibold text-slate-900">{pt.total_volume}</span>
                        </div>
                        <div className="my-2 h-10 w-full bg-slate-200 rounded-xs flex flex-col-reverse overflow-hidden">
                          <div style={{ height: `${posPct}%` }} className="bg-emerald-500 w-full" />
                          <div style={{ height: `${neuPct}%` }} className="bg-slate-400 w-full" />
                          <div style={{ height: `${negPct}%` }} className="bg-rose-500 w-full" />
                        </div>
                        <div className="text-[10px] font-mono text-slate-500 flex justify-between">
                          <span>Eng</span>
                          <span className="font-semibold text-slate-700">{pt.avg_engagement}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>

          {/* Trending Topics Table */}
          <div className="bg-white border border-slate-200 rounded-xs shadow-2xs overflow-hidden">
            <div className="p-4 border-b border-slate-200 flex items-center justify-between">
              <div>
                <h2 className="text-sm font-semibold text-slate-900 font-sans">
                  Ranked Topic Intelligence Ledger
                </h2>
                <p className="text-[11px] text-slate-500 font-sans">
                  Scored via 4-signal base momentum modulated by exponential recency decay.
                </p>
              </div>
              <Link
                href="/topics"
                className="text-xs font-mono font-medium text-slate-700 hover:text-slate-900 flex items-center gap-1"
              >
                View All Topics &rarr;
              </Link>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 font-mono text-[11px] text-slate-500 uppercase tracking-wider">
                    <th className="py-2.5 px-4">Topic Cluster</th>
                    <th className="py-2.5 px-4">Classification</th>
                    <th className="py-2.5 px-4 font-mono-numbers">TrendScore</th>
                    <th className="py-2.5 px-4 font-mono-numbers">Volume</th>
                    <th className="py-2.5 px-4 font-mono-numbers">Growth</th>
                    <th className="py-2.5 px-4">Mathematical Rationale</th>
                    <th className="py-2.5 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-sans">
                  {summary.top_trends.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="py-8 text-center text-slate-400 font-mono">
                        No trend snapshots available.
                      </td>
                    </tr>
                  ) : (
                    summary.top_trends.map((trend) => (
                      <tr key={trend.id} className="hover:bg-slate-50/80 transition-colors">
                        <td className="py-3 px-4 font-medium text-slate-900">
                          <Link
                            href={`/topics/${trend.topic_id}`}
                            className="hover:underline hover:text-sky-700 font-semibold"
                          >
                            {trend.topic_name || "Topic Cluster"}
                          </Link>
                        </td>
                        <td className="py-3 px-4">
                          {getClassificationBadge(trend.classification)}
                        </td>
                        <td className="py-3 px-4 font-mono font-semibold text-slate-900">
                          <div className="flex items-center gap-2">
                            <span>{trend.trend_score.toFixed(4)}</span>
                            <div className="w-12 h-1.5 bg-slate-100 rounded-xs overflow-hidden">
                              <div
                                style={{ width: `${Math.round(trend.trend_score * 100)}%` }}
                                className={`h-full ${
                                  trend.trend_score >= 0.70
                                    ? "bg-amber-500"
                                    : trend.trend_score >= 0.60
                                    ? "bg-teal-500"
                                    : trend.trend_score >= 0.40
                                    ? "bg-slate-400"
                                    : "bg-rose-400"
                                }`}
                              />
                            </div>
                          </div>
                        </td>
                        <td className="py-3 px-4 font-mono text-slate-700">
                          {trend.volume_current}
                        </td>
                        <td className="py-3 px-4 font-mono">
                          {trend.volume_growth_pct !== null && trend.volume_growth_pct !== undefined ? (
                            <span
                              className={
                                trend.volume_growth_pct > 0
                                  ? "text-emerald-700 font-medium"
                                  : trend.volume_growth_pct < 0
                                  ? "text-rose-700 font-medium"
                                  : "text-slate-500"
                              }
                            >
                              {trend.volume_growth_pct > 0 ? "+" : ""}
                              {trend.volume_growth_pct.toFixed(1)}%
                            </span>
                          ) : (
                            <span className="text-slate-400">—</span>
                          )}
                        </td>
                        <td className="py-3 px-4 text-slate-500 max-w-xs truncate text-[11px]" title={trend.explanation}>
                          {trend.explanation}
                        </td>
                        <td className="py-3 px-4 text-right">
                          <Link
                            href={`/topics/${trend.topic_id}`}
                            className="inline-flex items-center px-2 py-1 rounded-xs border border-slate-200 text-slate-700 bg-white hover:bg-slate-100 text-[11px] font-mono transition-colors"
                          >
                            Inspect &rarr;
                          </Link>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Bottom Grid: Entities, Keywords & Hashtags */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Top Entities */}
            <div className="bg-white border border-slate-200 rounded-xs p-4 shadow-2xs space-y-3">
              <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                <span className="text-xs font-semibold text-slate-900 font-sans flex items-center gap-1.5">
                  <Users className="w-3.5 h-3.5 text-slate-500" />
                  Named Entities (NER)
                </span>
                <span className="text-[10px] font-mono text-slate-400">spaCy en_core_web_sm</span>
              </div>
              <div className="space-y-1.5">
                {summary.top_entities.length === 0 ? (
                  <p className="text-xs text-slate-400 font-mono py-2">No entities detected.</p>
                ) : (
                  summary.top_entities.map((e, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between py-1 px-1.5 rounded-xs hover:bg-slate-50 text-xs"
                    >
                      <span className="font-medium text-slate-800 truncate mr-2">{e.text}</span>
                      <div className="flex items-center gap-1.5 shrink-0">
                        <span className="font-mono text-[10px] px-1 py-0.2 rounded-xs bg-slate-100 text-slate-600 border border-slate-200">
                          {e.label}
                        </span>
                        <span className="font-mono text-[11px] text-slate-500 font-semibold">{e.frequency}</span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Emerging Hashtags */}
            <div className="bg-white border border-slate-200 rounded-xs p-4 shadow-2xs space-y-3">
              <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                <span className="text-xs font-semibold text-slate-900 font-sans flex items-center gap-1.5">
                  <Hash className="w-3.5 h-3.5 text-slate-500" />
                  Hashtag Velocity
                </span>
                <span className="text-[10px] font-mono text-slate-400">Frequency & Delta</span>
              </div>
              <div className="space-y-1.5">
                {summary.top_hashtags.length === 0 ? (
                  <p className="text-xs text-slate-400 font-mono py-2">No hashtags found.</p>
                ) : (
                  summary.top_hashtags.map((h, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between py-1 px-1.5 rounded-xs hover:bg-slate-50 text-xs"
                    >
                      <span className="font-mono text-slate-800">#{h.keyword}</span>
                      <div className="flex items-center gap-2">
                        {h.growth_rate !== null && h.growth_rate !== undefined && (
                          <span
                            className={`font-mono text-[10px] ${
                              h.growth_rate > 0
                                ? "text-emerald-700"
                                : h.growth_rate < 0
                                ? "text-rose-700"
                                : "text-slate-400"
                            }`}
                          >
                            {h.growth_rate > 0 ? "+" : ""}
                            {h.growth_rate.toFixed(0)}%
                          </span>
                        )}
                        <span className="font-mono text-[11px] text-slate-500 font-semibold">{h.frequency}</span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* TF-IDF Keywords */}
            <div className="bg-white border border-slate-200 rounded-xs p-4 shadow-2xs space-y-3">
              <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                <span className="text-xs font-semibold text-slate-900 font-sans flex items-center gap-1.5">
                  <BarChart2 className="w-3.5 h-3.5 text-slate-500" />
                  Salient Keywords
                </span>
                <span className="text-[10px] font-mono text-slate-400">c-TF-IDF Score</span>
              </div>
              <div className="space-y-1.5">
                {summary.top_keywords.length === 0 ? (
                  <p className="text-xs text-slate-400 font-mono py-2">No keywords available.</p>
                ) : (
                  summary.top_keywords.map((k, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between py-1 px-1.5 rounded-xs hover:bg-slate-50 text-xs"
                    >
                      <span className="text-slate-800 truncate mr-2">{k.keyword}</span>
                      <span className="font-mono text-[11px] text-sky-700 font-semibold">
                        {k.tfidf_score.toFixed(4)}
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
