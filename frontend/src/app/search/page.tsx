"use client";

import React, { useCallback, useEffect, useState } from "react";
import {
  Filter,
  Loader2,
  MessageSquare,
  Search,
  ThumbsUp,
} from "lucide-react";
import { api, PostItem } from "@/lib/api";

export default function SearchPage() {
  const [posts, setPosts] = useState<PostItem[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);

  // Filters
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [sentimentFilter, setSentimentFilter] = useState<string>("");
  const [platformFilter, setPlatformFilter] = useState<string>("");
  const [page, setPage] = useState<number>(0);
  const pageSize = 25;

  const executeSearch = useCallback(async () => {
    try {
      setLoading(true);
      const res = await api.searchPosts({
        q: searchTerm.trim() || undefined,
        sentiment: sentimentFilter || undefined,
        platform: platformFilter || undefined,
        limit: pageSize,
        offset: page * pageSize,
      });
      setPosts(res.items || []);
      setTotal(res.total || 0);
    } catch (err) {
      console.error("Search failed:", err);
    } finally {
      setLoading(false);
    }
  }, [searchTerm, sentimentFilter, platformFilter, page]);

  useEffect(() => {
    executeSearch();
  }, [executeSearch]);

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(0);
    executeSearch();
  };

  const getSentimentBadge = (sent?: string) => {
    switch (sent) {
      case "positive":
        return (
          <span className="px-1.5 py-0.5 rounded-xs text-[10px] font-mono font-medium bg-emerald-50 text-emerald-800 border border-emerald-200">
            Positive
          </span>
        );
      case "negative":
        return (
          <span className="px-1.5 py-0.5 rounded-xs text-[10px] font-mono font-medium bg-rose-50 text-rose-800 border border-rose-200">
            Negative
          </span>
        );
      default:
        return (
          <span className="px-1.5 py-0.5 rounded-xs text-[10px] font-mono font-medium bg-slate-100 text-slate-700 border border-slate-200">
            Neutral
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900 font-sans">
            Post Explorer & Corpus Search
          </h1>
          <p className="text-xs text-slate-500 mt-1 font-sans">
            Inspect raw social data, filter by sentiment classifications, social platforms, and textual queries.
          </p>
        </div>

        <div className="text-xs font-mono text-slate-500 self-start sm:self-auto">
          Corpus Results: <span className="font-semibold text-slate-900 font-mono-numbers">{total.toLocaleString()}</span>
        </div>
      </div>

      {/* Search and Filters Bar */}
      <form onSubmit={handleFormSubmit} className="bg-white p-4 border border-slate-200 rounded-xs shadow-2xs space-y-3">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search post text, hashtags, or keywords..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xs focus:outline-hidden focus:border-slate-400 font-sans"
            />
          </div>

          <button
            type="submit"
            className="px-4 py-2 bg-slate-900 text-white rounded-xs text-xs font-medium hover:bg-slate-800 transition-colors shadow-xs cursor-pointer font-sans"
          >
            Search Posts
          </button>
        </div>

        {/* Facet Dropdowns */}
        <div className="flex flex-wrap items-center gap-3 pt-2 border-t border-slate-100 text-xs font-sans">
          <div className="flex items-center gap-1.5 text-slate-500 font-mono text-[11px]">
            <Filter className="w-3.5 h-3.5" />
            <span>Facets:</span>
          </div>

          {/* Sentiment Filter */}
          <select
            value={sentimentFilter}
            onChange={(e) => {
              setSentimentFilter(e.target.value);
              setPage(0);
            }}
            aria-label="Filter by sentiment"
            className="px-2.5 py-1 text-xs bg-slate-50 border border-slate-200 rounded-xs font-mono text-slate-700"
          >
            <option value="">All Sentiments</option>
            <option value="positive">Positive</option>
            <option value="neutral">Neutral</option>
            <option value="negative">Negative</option>
          </select>

          {/* Platform Filter */}
          <select
            value={platformFilter}
            onChange={(e) => {
              setPlatformFilter(e.target.value);
              setPage(0);
            }}
            aria-label="Filter by platform"
            className="px-2.5 py-1 text-xs bg-slate-50 border border-slate-200 rounded-xs font-mono text-slate-700"
          >
            <option value="">All Platforms</option>
            <option value="twitter">Twitter / X</option>
            <option value="reddit">Reddit</option>
            <option value="bluesky">Bluesky</option>
          </select>

          {(searchTerm || sentimentFilter || platformFilter) && (
            <button
              type="button"
              onClick={() => {
                setSearchTerm("");
                setSentimentFilter("");
                setPlatformFilter("");
                setPage(0);
              }}
              className="text-[11px] font-mono text-slate-500 hover:text-slate-900 underline"
            >
              Reset Filters
            </button>
          )}
        </div>
      </form>

      {/* Results Feed */}
      <div className="bg-white border border-slate-200 rounded-xs shadow-2xs overflow-hidden">
        {loading ? (
          <div className="py-16 text-center text-xs font-mono text-slate-500 flex items-center justify-center gap-2">
            <Loader2 className="w-4 h-4 animate-spin text-slate-600" />
            Querying corpus posts...
          </div>
        ) : posts.length === 0 ? (
          <div className="py-16 text-center text-xs font-mono text-slate-400 space-y-1">
            <p className="font-semibold text-slate-700 font-sans">No matching records found.</p>
            <p className="text-[11px] text-slate-500 font-sans">Try searching with broader terms or clear categorical filters.</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {posts.map((p) => (
              <div key={p.id} className="p-4 hover:bg-slate-50/70 transition-colors space-y-2">
                <div className="flex flex-wrap items-center justify-between gap-2 text-[11px] font-mono text-slate-500">
                  <div className="flex items-center gap-2">
                    {p.platform && (
                      <span className="px-1.5 py-0.5 rounded-xs bg-slate-100 text-slate-700 uppercase border border-slate-200 text-[10px]">
                        {p.platform}
                      </span>
                    )}
                    {p.author_id && <span>@{p.author_id}</span>}
                    <span>
                      {new Date(p.timestamp).toLocaleDateString("en-US", {
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

                  <div className="flex items-center gap-2">
                    {p.topic_name && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded-xs bg-sky-50 text-sky-800 border border-sky-200">
                        {p.topic_name}
                      </span>
                    )}
                    {getSentimentBadge(p.sentiment)}
                  </div>
                </div>

                <p className="text-xs text-slate-900 font-sans leading-relaxed">
                  {p.original_text}
                </p>

                {/* Engagement & Hashtags footer */}
                <div className="flex items-center justify-between pt-1 text-[11px] font-mono text-slate-500">
                  <div className="flex items-center gap-3">
                    {p.likes !== undefined && p.likes !== null && (
                      <span className="flex items-center gap-1">
                        <ThumbsUp className="w-3 h-3 text-slate-400" />
                        {p.likes}
                      </span>
                    )}
                    {p.comments !== undefined && p.comments !== null && (
                      <span className="flex items-center gap-1">
                        <MessageSquare className="w-3 h-3 text-slate-400" />
                        {p.comments}
                      </span>
                    )}
                  </div>

                  {p.hashtags && p.hashtags.length > 0 && (
                    <div className="flex gap-1 flex-wrap">
                      {p.hashtags.map((h, i) => (
                        <span key={i} className="text-slate-400">
                          #{h}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Pagination Toolbar */}
        {!loading && total > pageSize && (
          <div className="p-3 border-t border-slate-200 bg-slate-50/70 flex items-center justify-between text-xs font-mono">
            <span className="text-slate-500">
              Showing {page * pageSize + 1}–{Math.min((page + 1) * pageSize, total)} of {total}
            </span>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={page === 0}
                className="px-2.5 py-1 rounded-xs border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                &larr; Prev
              </button>
              <span className="text-slate-600 px-1 font-semibold">
                {page + 1} / {Math.ceil(total / pageSize)}
              </span>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={(page + 1) * pageSize >= total}
                className="px-2.5 py-1 rounded-xs border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next &rarr;
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
