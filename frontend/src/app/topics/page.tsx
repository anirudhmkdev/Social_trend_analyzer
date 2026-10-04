"use client";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { useAnalysis, ContextToolbar, AnalysisState, ModelWarning } from "@/components/AnalysisContext";
import { TrendTable } from "@/components/TrendTable";
import { ErrorNotice, Loading } from "@/components/Feedback";
import { useResource } from "@/hooks/useResource";
export default function Topics() {
  const ctx = useAnalysis(), search = useSearchParams();
  const classification = search.get("classification") || "", q = search.get("q") || "";
  const resource = useResource(`${ctx.query}:${classification}:${q}`, () => api.getTopics(ctx.read, classification, q), !ctx.loading && !ctx.error && ctx.run?.status === "completed");
  return <><div className="page-heading"><div><p className="eyebrow">Topic discovery</p><h1>Trends & Topics</h1><p className="muted">Investigate coherent clusters and their latest activity.</p></div></div><ContextToolbar /><AnalysisState /><ModelWarning />
    <form className="filter-row" onSubmit={event => { event.preventDefault(); const data = new FormData(event.currentTarget); ctx.select({ q: String(data.get("q") || ""), classification: String(data.get("classification") || "") }); }}>
      <label>Topic keywords<input name="q" defaultValue={q} key={q} placeholder="Search topic labels or terms" /></label><label>Classification<select name="classification" defaultValue={classification} key={classification}><option value="">All classifications</option>{["emerging", "rising", "stable", "declining"].map(value => <option key={value}>{value}</option>)}</select></label><button className="primary" type="submit">Apply filters</button><button type="button" onClick={() => ctx.select({ q: undefined, classification: undefined })}>Clear</button>
    </form>{resource.loading && <Loading />}<ErrorNotice error={resource.error} retry={resource.retry} />
    {resource.data && <section className="panel"><div className="section-heading"><h2>{resource.data.total_topics} matching topics</h2><span className="muted">{resource.data.outlier_count} unclassified posts in this run</span></div><TrendTable trends={resource.data.topics.flatMap(topic => topic.latest_trend ? [topic.latest_trend] : [])} query={ctx.query} /></section>}
  </>;
}
