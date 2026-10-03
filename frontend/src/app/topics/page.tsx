"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowDownRight,
  ArrowUpRight,
  Flame,
  Layers,
  Loader2,
  RefreshCw,
  Search,
} from "lucide-react";
import { api, TopicItem } from "@/lib/api";

export default function TopicsPage() {
  const [topics, setTopics] = useState<TopicItem[]>([]);
  const [filterClass, setFilterClass] = useState<string>("all");
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [loading, setLoading] = useState(true);

  const fetchTopics = async () => {
    try {
      setLoading(true);
      const res = await api.getTopics();
      setTopics(res.topics || []);
    } catch (err) {
      console.error("Failed to load topics:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTopics();
  }, []);

  const filteredTopics = topics.filter((t) => {
    if (t.is_outlier) return false;
    if (filterClass !== "all" && t.trend_classification !== filterClass) {
      return false;
    }
    if (searchTerm.trim()) {
      const q = searchTerm.toLowerCase();
      const matchName = t.display_name.toLowerCase().includes(q);
      const matchKw = t.keywords.some((k) => k.word.toLowerCase().includes(q));
      if (!matchName && !matchKw) return false;
    }
    return true;
  });

  const getClassificationBadge = (cls?: string) => {
    switch (cls) {
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold tracking-tight text-slate-900 font-sans">
              Thematic Topic Clusters
            </h1>
            <span className="font-mono text-xs px-2 py-0.5 rounded-xs bg-slate-100 text-slate-700 border border-slate-200">
              {filteredTopics.length} Discovered
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1 font-sans">
            Unsupervised semantic discovery via Sentence-Transformers, UMAP dimensional reduction, and HDBSCAN density clustering.
          </p>
        </div>

        <button
          onClick={fetchTopics}
          disabled={loading}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xs border border-slate-200 bg-white text-xs font-medium text-slate-700 hover:bg-slate-50 transition-colors shadow-2xs cursor-pointer self-start sm:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-white p-3 border border-slate-200 rounded-xs shadow-2xs">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search topics by name or salient keyword..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-8 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xs focus:outline-hidden focus:border-slate-400 font-sans"
          />
        </div>

        <div className="flex items-center gap-1.5 font-mono text-xs overflow-x-auto">
          {(["all", "emerging", "rising", "stable", "declining"] as const).map((cls) => (
            <button
              key={cls}
              onClick={() => setFilterClass(cls)}
              className={`px-2.5 py-1 rounded-xs transition-colors capitalize ${
                filterClass === cls
                  ? "bg-slate-900 text-white font-medium"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              {cls}
            </button>
          ))}
        </div>
      </div>

      {/* Topics Ledger Grid */}
      {loading ? (
        <div className="py-16 text-center text-xs font-mono text-slate-500 flex items-center justify-center gap-2">
          <Loader2 className="w-4 h-4 animate-spin text-slate-600" />
          Loading Topic Clusters...
        </div>
      ) : filteredTopics.length === 0 ? (
        <div className="py-16 text-center border border-dashed border-slate-200 rounded-xs bg-white space-y-2">
          <Layers className="w-8 h-8 text-slate-400 mx-auto" />
          <p className="text-xs font-semibold text-slate-700 font-sans">No Topics Match Query</p>
          <p className="text-[11px] text-slate-500 font-sans">Try adjusting search keywords or category filters.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredTopics.map((topic) => (
            <div
              key={topic.id}
              className="bg-white border border-slate-200 rounded-xs p-4 shadow-2xs hover:border-slate-300 transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between gap-2">
                  <span className="font-mono text-[10px] text-slate-400">
                    Cluster #{topic.topic_index}
                  </span>
                  {getClassificationBadge(topic.trend_classification)}
                </div>

                <Link
                  href={`/topics/${topic.id}`}
                  className="block mt-2 font-semibold text-sm text-slate-900 hover:text-sky-700 font-sans leading-snug"
                >
                  {topic.display_name}
                </Link>

                {/* Keywords Chips */}
                <div className="mt-3 flex flex-wrap gap-1">
                  {topic.keywords.slice(0, 5).map((kw, i) => (
                    <span
                      key={i}
                      className="text-[10px] font-mono px-1.5 py-0.5 rounded-xs bg-slate-100 text-slate-600 border border-slate-200"
                    >
                      {kw.word}
                    </span>
                  ))}
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs font-mono">
                <div className="text-slate-500">
                  <span className="font-semibold text-slate-800">{topic.post_count}</span> posts
                </div>

                <div className="flex items-center gap-3">
                  {topic.trend_score !== undefined && (
                    <span className="text-slate-700">
                      Score: <strong className="text-slate-900 font-mono-numbers">{topic.trend_score.toFixed(4)}</strong>
                    </span>
                  )}
                  <Link
                    href={`/topics/${topic.id}`}
                    className="text-sky-700 hover:underline font-semibold"
                  >
                    Inspect &rarr;
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
