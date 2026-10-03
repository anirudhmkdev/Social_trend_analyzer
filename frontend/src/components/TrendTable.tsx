import Link from "next/link";
import { TrendSnapshot } from "@/lib/api";
import { Sparkline } from "./ActivityChart";

export function TrendTable({ trends, query }: { trends: TrendSnapshot[]; query: string }) {
  return <div className="table-wrap"><table className="trend-table"><caption className="sr-only">Topics ranked by trend score in the selected dataset and analysis run</caption><thead><tr>{["Topic", "Classification", "TrendScore", "Volume", "Growth", "Sentiment", "Activity", "Reason"].map(header => <th scope="col" key={header}>{header}</th>)}</tr></thead><tbody>{trends.length ? trends.map(trend => {
    const sentiments = [["Positive", trend.sentiment_positive_pct || 0], ["Neutral", trend.sentiment_neutral_pct || 0], ["Negative", trend.sentiment_negative_pct || 0]] as const;
    const dominant = [...sentiments].sort((a, b) => b[1] - a[1])[0];
    const guarded = trend.volume_current < trend.min_posts_for_trend;
    return <tr key={trend.topic_id}><th scope="row"><Link href={`/topics/${trend.topic_id}?${query}`}>{trend.topic_name || "Unnamed topic"}</Link></th>
      <td><span className={`classification ${trend.classification}`}>{trend.classification}</span>{guarded && <span className="muted guard">Insufficient current volume ({trend.volume_current} &lt; {trend.min_posts_for_trend})</span>}</td>
      <td className="numeric">{trend.trend_score.toFixed(3)}</td><td className="numeric">{trend.volume_current}</td><td className="numeric">{trend.volume_growth_pct === null ? "—" : `${trend.volume_growth_pct > 0 ? "+" : ""}${trend.volume_growth_pct.toFixed(0)}%`}</td>
      <td>{dominant[1] ? dominant[0] : "No posts"}</td><td><Sparkline values={trend.activity} /></td><td className="reason"><details><summary>{trend.explanation.split(". ")[0]}</summary><p>{trend.explanation}</p></details></td></tr>;
  }) : <tr><td colSpan={8} className="empty-state">No topics match this context. Adjust the filters or inspect the analysis output.</td></tr>}</tbody></table></div>;
}
