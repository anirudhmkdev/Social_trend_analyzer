"use client";
import { use } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { useAnalysis, ContextToolbar, AnalysisState, ModelWarning } from "@/components/AnalysisContext";
import { ActivityChart } from "@/components/ActivityChart";
import { TrendTable } from "@/components/TrendTable";
import { ErrorNotice, Loading } from "@/components/Feedback";
import { useResource } from "@/hooks/useResource";
export default function TopicDetail({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params), ctx = useAnalysis();
  const resource = useResource(`${id}:${ctx.query}`, () => api.getTopicDetail(id, ctx.run?.id, ctx.read), !ctx.loading && !ctx.error && ctx.run?.status === "completed");
  const detail = resource.data;
  return <><Link href={`/topics?${ctx.query}`}>← Trends & Topics</Link><div className="page-heading"><div><p className="eyebrow">Topic investigation</p><h1>{detail?.topic.display_name || "Topic detail"}</h1><p className="muted">Evidence from the selected run. Changing runs may make this topic unavailable.</p></div></div><ContextToolbar /><AnalysisState /><ModelWarning />{resource.loading && <Loading />}<ErrorNotice error={resource.error} retry={resource.retry} />
    {detail && <>
      <section className="panel"><h2>Latest trend explanation</h2><TrendTable trends={detail.topic.latest_trend ? [detail.topic.latest_trend] : []} query={ctx.query} /></section>
      <div className="metric-strip"><div><span>Assigned posts</span><strong className="numeric">{detail.topic.post_count}</strong></div>{Object.entries(detail.sentiment_distribution).map(([label, count]) => <div key={label}><span>{label}</span><strong className="numeric">{count.toFixed(1)}%</strong></div>)}{Object.entries(detail.avg_engagement).map(([label, value]) => <div key={label}><span>Avg. {label}</span><strong className="numeric">{value === null ? "Unavailable" : value.toFixed(1)}</strong></div>)}</div>
      <section className="panel"><ActivityChart points={detail.timeline} /></section>
      <div className="evidence-grid"><section className="panel"><h2>Topic terms</h2><p className="muted">c-TF-IDF weights for BERTopic; TF-IDF for small corpora.</p><dl className="evidence-list">{detail.topic.keywords.map(item => <div key={item.word}><dt>{item.word}</dt><dd className="numeric">{item.score.toFixed(4)}</dd></div>)}</dl></section><section className="panel"><h2>Entities</h2><dl className="evidence-list">{detail.entities.map(item => <div key={`${item.label}:${item.text}`}><dt>{item.text} <small>{item.label}</small></dt><dd className="numeric">{item.frequency}</dd></div>)}</dl>{!detail.entities.length && <p>No named entities available.</p>}</section><section className="panel"><h2>Keywords & hashtags</h2><dl className="evidence-list">{detail.keywords.slice(0, 8).map(item => <div key={item.keyword}><dt>{item.keyword}</dt><dd className="numeric">{item.frequency}</dd></div>)}</dl><p>{detail.hashtags.map(item => `${item.keyword} (${item.frequency})`).join(" · ") || "No hashtags."}</p></section></div>
      <section className="panel"><div className="section-heading"><h2>Representative posts</h2><Link href={`/explorer?${ctx.query}&topic=${id}`}>Explore all assigned posts →</Link></div><p className="muted">Highest assignment probabilities. Aggregates above cover the complete topic.</p>{detail.sample_posts.map(post => <article className="post-row" key={post.id}><p>{post.original_text}</p><p className="muted numeric">{new Date(post.timestamp).toLocaleString()} · {post.platform || "Unknown platform"} · {post.sentiment || "Unscored"} · {post.probability === null || post.probability === undefined ? "No probability" : post.probability.toFixed(3)}</p></article>)}</section>
      <section className="panel"><h2>Trend history</h2><div className="table-wrap"><table><caption className="sr-only">Topic scores and classifications by bucket</caption><thead><tr>{["UTC bucket", "Posts", "Score", "Classification", "Explanation"].map(label => <th scope="col" key={label}>{label}</th>)}</tr></thead><tbody>{detail.trend_history.map(row => <tr key={row.id}><th scope="row" className="numeric">{new Date(row.window_start).toISOString().slice(0, 16)}</th><td>{row.volume_current}</td><td className="numeric">{row.trend_score.toFixed(3)}</td><td>{row.classification}</td><td>{row.explanation}</td></tr>)}</tbody></table></div></section>
      <details className="panel"><summary>Model identity and raw cluster provenance</summary><p>Model topic index: <span className="numeric">{detail.topic.topic_index}</span>. Labels are derived locally from keywords and do not establish ground truth.</p><pre className="json-evidence">{JSON.stringify(detail.topic.model_metadata || {}, null, 2)}</pre></details>
    </>}
  </>;
}
