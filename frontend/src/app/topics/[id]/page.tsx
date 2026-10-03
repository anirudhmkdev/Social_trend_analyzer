"use client";

import React, { use, useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowDownRight,
  ArrowLeft,
  ArrowUpRight,
  Flame,
  Loader2,
  Sparkles,
} from "lucide-react";
import {
  api,
  TopicDetailResponse,
  TrendSnapshot,
} from "@/lib/api";

export default function TopicDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const topicId = resolvedParams.id;

  const [detail, setDetail] = useState<TopicDetailResponse | null>(null);
  const [trajectory, setTrajectory] = useState<TrendSnapshot[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [det, traj] = await Promise.all([
          api.getTopicDetail(topicId),
          api.getTopicTrendHistory(topicId, "daily"),
        ]);
        setDetail(det);
        setTrajectory(traj || []);
      } catch (err) {
        console.error("Failed to load topic details:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [topicId]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] gap-3 text-slate-500 font-mono text-xs">
        <Loader2 className="w-5 h-5 animate-spin text-slate-700" />
        Loading Topic Deep-Dive...
      </div>
    );
  }

  if (!detail) {
    return (
      <div className="py-12 text-center space-y-3">
        <p className="text-sm font-semibold text-slate-800">Topic Not Found</p>
        <Link href="/topics" className="text-xs font-mono text-sky-700 hover:underline">
          &larr; Return to Topics
        </Link>
      </div>
    );
  }

  const { topic, sentiment_distribution, avg_engagement, sample_posts } = detail;
  const latestSnapshot = trajectory.length > 0 ? trajectory[trajectory.length - 1] : null;

  const getClassificationBadge = (cls?: string) => {
    switch (cls) {
      case "emerging":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-xs text-xs font-mono font-medium bg-amber-50 text-amber-800 border border-amber-200">
            <Flame className="w-3.5 h-3.5 text-amber-600" />
            Emerging Surge
          </span>
        );
      case "rising":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-xs text-xs font-mono font-medium bg-teal-50 text-teal-800 border border-teal-200">
            <ArrowUpRight className="w-3.5 h-3.5 text-teal-600" />
            Rising Trend
          </span>
        );
      case "declining":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-xs text-xs font-mono font-medium bg-rose-50 text-rose-800 border border-rose-200">
            <ArrowDownRight className="w-3.5 h-3.5 text-rose-600" />
            Declining Momentum
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-xs text-xs font-mono font-medium bg-slate-100 text-slate-700 border border-slate-200">
            Stable
          </span>
        );
    }
  };

  const posCount = sentiment_distribution?.positive || 0;
  const neuCount = sentiment_distribution?.neutral || 0;
  const negCount = sentiment_distribution?.negative || 0;
  const totSent = posCount + neuCount + negCount;
  const posPct = totSent > 0 ? Math.round((posCount / totSent) * 100) : 0;
  const neuPct = totSent > 0 ? Math.round((neuCount / totSent) * 100) : 0;
  const negPct = totSent > 0 ? Math.round((negCount / totSent) * 100) : 0;

  return (
    <div className="space-y-6">
      {/* Back link & breadcrumb */}
      <div>
        <Link
          href="/topics"
          className="inline-flex items-center gap-1.5 text-xs font-mono text-slate-500 hover:text-slate-900 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to Topic Clusters
        </Link>
      </div>

      {/* Hero Topic Header */}
      <div className="bg-white border border-slate-200 rounded-xs p-6 shadow-2xs space-y-4">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
          <div className="space-y-1.5 max-w-2xl">
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs px-2 py-0.5 rounded-xs bg-slate-100 text-slate-600 border border-slate-200">
                Cluster #{topic.topic_index}
              </span>
              {latestSnapshot && getClassificationBadge(latestSnapshot.classification)}
            </div>
            <h1 className="text-xl md:text-2xl font-bold tracking-tight text-slate-900 font-sans">
              {topic.display_name}
            </h1>
            <p className="text-xs text-slate-500 font-sans">
              Comprehensive NLP analytical profile including statistical trajectory, sentiment breakdown, and representative texts.
            </p>
          </div>

          {/* TrendScore Callout Tile */}
          {latestSnapshot && (
            <div className="bg-slate-50 border border-slate-200 rounded-xs p-3.5 shrink-0 min-w-48 text-right font-mono">
              <div className="text-[11px] text-slate-500 uppercase tracking-wider">TrendScore</div>
              <div className="text-3xl font-bold text-slate-900 mt-1">
                {latestSnapshot.trend_score.toFixed(4)}
              </div>
              <div className="mt-2 w-full h-1.5 bg-slate-200 rounded-xs overflow-hidden">
                <div
                  style={{ width: `${Math.round(latestSnapshot.trend_score * 100)}%` }}
                  className={`h-full ${
                    latestSnapshot.trend_score >= 0.70
                      ? "bg-amber-500"
                      : latestSnapshot.trend_score >= 0.60
                      ? "bg-teal-500"
                      : latestSnapshot.trend_score >= 0.40
                      ? "bg-slate-500"
                      : "bg-rose-500"
                  }`}
                />
              </div>
            </div>
          )}
        </div>

        {/* c-TF-IDF Salient Keyword Chips */}
        <div className="pt-3 border-t border-slate-100">
          <div className="text-[11px] font-mono text-slate-400 uppercase tracking-wider mb-2">
            Salient c-TF-IDF Keywords & Importance Weights
          </div>
          <div className="flex flex-wrap gap-1.5">
            {topic.keywords.map((kw, idx) => (
              <span
                key={idx}
                className="inline-flex items-center gap-1.5 px-2 py-1 rounded-xs bg-slate-50 text-slate-800 border border-slate-200 text-xs font-mono"
              >
                <span>{kw.word}</span>
                <span className="text-[10px] text-slate-400 font-semibold">{kw.score.toFixed(3)}</span>
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Mathematical Rationale & Stats Banner */}
      {latestSnapshot && (
        <div className="bg-white border border-slate-200 rounded-xs p-4 shadow-2xs">
          <div className="text-xs font-semibold text-slate-900 font-sans flex items-center gap-1.5 mb-2">
            <Sparkles className="w-3.5 h-3.5 text-sky-600" />
            Empirical Trend Rationale
          </div>
          <p className="text-xs text-slate-700 font-mono leading-relaxed bg-slate-50 p-3 rounded-xs border border-slate-200">
            {latestSnapshot.explanation}
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-3 pt-3 border-t border-slate-100 font-mono text-xs">
            <div>
              <span className="text-[10px] text-slate-400 block uppercase">Burstiness</span>
              <span className="font-semibold text-slate-800">
                {latestSnapshot.burst_score !== null && latestSnapshot.burst_score !== undefined
                  ? `${latestSnapshot.burst_score.toFixed(2)} σ`
                  : "0.00 σ"}
              </span>
            </div>
            <div>
              <span className="text-[10px] text-slate-400 block uppercase">Velocity</span>
              <span className="font-semibold text-slate-800">
                {latestSnapshot.velocity !== null && latestSnapshot.velocity !== undefined
                  ? latestSnapshot.velocity.toFixed(3)
                  : "0.000"}
              </span>
            </div>
            <div>
              <span className="text-[10px] text-slate-400 block uppercase">Volume Growth</span>
              <span
                className={`font-semibold ${
                  (latestSnapshot.volume_growth_pct || 0) > 0
                    ? "text-emerald-700"
                    : (latestSnapshot.volume_growth_pct || 0) < 0
                    ? "text-rose-700"
                    : "text-slate-700"
                }`}
              >
                {(latestSnapshot.volume_growth_pct || 0) > 0 ? "+" : ""}
                {(latestSnapshot.volume_growth_pct || 0).toFixed(1)}%
              </span>
            </div>
            <div>
              <span className="text-[10px] text-slate-400 block uppercase">Recency Factor</span>
              <span className="font-semibold text-slate-800">
                {latestSnapshot.recency_score !== null && latestSnapshot.recency_score !== undefined
                  ? latestSnapshot.recency_score.toFixed(3)
                  : "1.000"}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Middle Row: Historical Trajectory Table & Sentiment Widget */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Trajectory Table (2 cols) */}
        <div className="lg:col-span-2 bg-white border border-slate-200 rounded-xs shadow-2xs overflow-hidden">
          <div className="p-4 border-b border-slate-200">
            <h2 className="text-sm font-semibold text-slate-900 font-sans">
              Chronological Trajectory (UTC Windows)
            </h2>
            <p className="text-[11px] text-slate-500 font-sans">
              Step-by-step evolution of volume, momentum, and signal changes across time.
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 font-mono text-[10px] text-slate-500 uppercase tracking-wider">
                  <th className="py-2.5 px-3">Window Start</th>
                  <th className="py-2.5 px-3">Classification</th>
                  <th className="py-2.5 px-3 font-mono-numbers">TrendScore</th>
                  <th className="py-2.5 px-3 font-mono-numbers">Volume</th>
                  <th className="py-2.5 px-3 font-mono-numbers">Growth</th>
                  <th className="py-2.5 px-3 font-mono-numbers">Burst (σ)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-mono text-xs">
                {trajectory.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-6 text-center text-slate-400">
                      No trajectory points available.
                    </td>
                  </tr>
                ) : (
                  trajectory.map((snap) => (
                    <tr key={snap.id} className="hover:bg-slate-50/70">
                      <td className="py-2 px-3 text-slate-600">
                        {new Date(snap.window_start).toLocaleDateString("en-US", {
                          month: "short",
                          day: "numeric",
                          year: "numeric",
                        })}
                      </td>
                      <td className="py-2 px-3">
                        {getClassificationBadge(snap.classification)}
                      </td>
                      <td className="py-2 px-3 font-semibold text-slate-900">
                        {snap.trend_score.toFixed(4)}
                      </td>
                      <td className="py-2 px-3 text-slate-700">
                        {snap.volume_current}
                      </td>
                      <td className="py-2 px-3">
                        {snap.volume_growth_pct !== null && snap.volume_growth_pct !== undefined ? (
                          <span
                            className={
                              snap.volume_growth_pct > 0
                                ? "text-emerald-700 font-semibold"
                                : snap.volume_growth_pct < 0
                                ? "text-rose-700 font-semibold"
                                : "text-slate-500"
                            }
                          >
                            {snap.volume_growth_pct > 0 ? "+" : ""}
                            {snap.volume_growth_pct.toFixed(0)}%
                          </span>
                        ) : (
                          "—"
                        )}
                      </td>
                      <td className="py-2 px-3 text-slate-600">
                        {snap.burst_score !== null && snap.burst_score !== undefined
                          ? snap.burst_score.toFixed(2)
                          : "0.00"}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Sentiment & Engagement Profile (1 col) */}
        <div className="bg-white border border-slate-200 rounded-xs p-4 shadow-2xs space-y-4">
          <div>
            <h2 className="text-sm font-semibold text-slate-900 font-sans">
              Cluster Sentiment & Engagement
            </h2>
            <p className="text-[11px] text-slate-500 font-sans">
              Twitter-RoBERTa sentiment classification across cluster posts.
            </p>
          </div>

          <div className="space-y-3 pt-2">
            <div>
              <div className="flex justify-between text-xs font-mono mb-1.5">
                <span className="text-emerald-700 font-semibold">Positive {posPct}% ({posCount})</span>
                <span className="text-slate-500">Neutral {neuPct}% ({neuCount})</span>
                <span className="text-rose-700 font-semibold">Negative {negPct}% ({negCount})</span>
              </div>
              <div className="w-full h-2.5 bg-slate-100 rounded-xs flex overflow-hidden">
                <div style={{ width: `${posPct}%` }} className="bg-emerald-500" />
                <div style={{ width: `${neuPct}%` }} className="bg-slate-400" />
                <div style={{ width: `${negPct}%` }} className="bg-rose-500" />
              </div>
            </div>

            <div className="pt-3 border-t border-slate-100 grid grid-cols-2 gap-3 text-xs font-mono">
              <div className="bg-slate-50 p-2.5 rounded-xs border border-slate-200">
                <span className="text-[10px] text-slate-400 uppercase block">Total Cluster Posts</span>
                <span className="text-lg font-bold text-slate-900">{topic.post_count}</span>
              </div>
              <div className="bg-slate-50 p-2.5 rounded-xs border border-slate-200">
                <span className="text-[10px] text-slate-400 uppercase block">Avg Engagement</span>
                <span className="text-lg font-bold text-slate-900">{avg_engagement.toFixed(1)}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Representative & Sample Posts Feed */}
      <div className="bg-white border border-slate-200 rounded-xs shadow-2xs">
        <div className="p-4 border-b border-slate-200 flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold text-slate-900 font-sans">
              Representative Post Feed
            </h2>
            <p className="text-[11px] text-slate-500 font-sans">
              Sample social posts clustered into this thematic topic.
            </p>
          </div>
          <span className="text-xs font-mono text-slate-400">
            {sample_posts?.length || 0} Sample Documents
          </span>
        </div>

        <div className="divide-y divide-slate-100">
          {!sample_posts || sample_posts.length === 0 ? (
            <div className="p-8 text-center text-xs font-mono text-slate-400">
              No sample posts recorded for this cluster.
            </div>
          ) : (
            sample_posts.map((post) => (
              <div key={post.id} className="p-4 hover:bg-slate-50/60 transition-colors space-y-2">
                <div className="flex items-center justify-between text-[11px] font-mono text-slate-500">
                  <div className="flex items-center gap-2">
                    {post.platform && (
                      <span className="px-1.5 py-0.5 rounded-xs bg-slate-100 text-slate-700 uppercase border border-slate-200 text-[10px]">
                        {post.platform}
                      </span>
                    )}
                    <span>
                      {new Date(post.timestamp).toLocaleDateString("en-US", {
                        month: "short",
                        day: "numeric",
                        year: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                        timeZone: "UTC",
                      })}{" "}
                      UTC
                    </span>
                  </div>
                  {post.likes !== undefined && post.likes !== null && (
                    <span>{post.likes} Likes</span>
                  )}
                </div>
                <p className="text-xs text-slate-900 font-sans leading-relaxed">
                  {post.text}
                </p>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
