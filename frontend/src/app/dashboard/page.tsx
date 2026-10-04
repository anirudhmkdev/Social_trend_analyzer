"use client";
import Link from "next/link";
import { api } from "@/lib/api";
import { useAnalysis, ContextToolbar, AnalysisState, ModelWarning } from "@/components/AnalysisContext";
import { useResource } from "@/hooks/useResource";
import { ActivityChart } from "@/components/ActivityChart";
import { TrendTable } from "@/components/TrendTable";
import { ErrorNotice, Loading } from "@/components/Feedback";
export default function Dashboard() {
  const ctx = useAnalysis();
  const ready = !ctx.loading && !ctx.error && ctx.run?.status === "completed";
  const resource = useResource(ctx.query, () => Promise.all([api.getDashboardSummary(ctx.read), api.getTimeline(ctx.read)]), ready);
  const summary = resource.data?.[0], timeline = resource.data?.[1];
  return <><div className="page-heading"><div><p className="eyebrow">Dataset intelligence</p><h1>What changed, and why?</h1><p className="muted">Ranked topics, activity and supporting evidence from the selected batch.</p></div><Link className="button" href="/datasets">Add Dataset</Link></div>
    <ContextToolbar /><AnalysisState /><ModelWarning />{resource.loading && <Loading />}<ErrorNotice error={resource.error} retry={resource.retry} />
    {summary && timeline && <>
      <section className="panel"><div className="section-heading"><div><h2>Ranked trends</h2><p className="muted">Latest {ctx.timeWindow} bucket. Scores rank activity; classification also applies a three-post guard.</p></div><Link href={`/topics?${ctx.query}`}>All trends & topics →</Link></div><TrendTable trends={summary.top_trends} query={ctx.query} /></section>
      <div className="metric-strip" aria-label="Selected analysis totals"><div><span>Posts in selection</span><strong className="numeric">{summary.total_posts.toLocaleString()}</strong></div><div><span>Topics in selection</span><strong className="numeric">{summary.total_topics}</strong></div>{Object.entries(summary.trend_classifications).map(([label, count]) => <div key={label}><span>{label}</span><strong className="numeric">{count}</strong></div>)}</div>
      <section className="panel"><ActivityChart points={timeline.timeline} /></section>
      <div className="evidence-grid"><section className="panel"><h2>Sentiment</h2><p className="muted">Model predictions across this selection.</p><dl className="evidence-list">{Object.entries(summary.sentiment_breakdown.counts).map(([label, count]) => <div key={label}><dt>{label}</dt><dd className="numeric">{count} · {summary.sentiment_breakdown.percentages[label as "positive" | "neutral" | "negative"].toFixed(1)}%</dd></div>)}</dl></section>
        <section className="panel"><h2>Entities</h2><p className="muted">Conservative spaCy mentions, counted by occurrence.</p><dl className="evidence-list">{summary.top_entities.map(entity => <div key={`${entity.label}:${entity.text}`}><dt>{entity.text} <small className="muted">{entity.label}</small></dt><dd className="numeric">{entity.frequency}</dd></div>)}</dl>{!summary.top_entities.length && <p>No entities available. Check model status in Analysis.</p>}</section>
        <section className="panel"><h2>Keywords & hashtags</h2><p className="muted">Post frequency and corpus TF-IDF; topic terms use c-TF-IDF.</p><dl className="evidence-list">{summary.top_keywords.slice(0, 7).map(item => <div key={item.keyword}><dt>{item.keyword}</dt><dd className="numeric">{item.frequency}</dd></div>)}</dl><p>{summary.top_hashtags.slice(0, 8).map(item => `${item.keyword} (${item.frequency})`).join(" · ") || "No hashtags in this selection."}</p></section></div>
    </>}
  </>;
}
