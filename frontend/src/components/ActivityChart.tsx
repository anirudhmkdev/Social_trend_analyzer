"use client";
import { useState } from "react";
import { TimelinePoint } from "@/lib/api";

export function ActivityChart({ points }: { points: TimelinePoint[] }) {
  const [active, setActive] = useState<number | null>(null);
  if (!points.length) return <p className="empty-state">No activity in the selected context.</p>;
  const width = 800, height = 210, left = 38, top = 12, bottom = 35;
  const plotHeight = height - top - bottom, plotWidth = width - left - 12;
  const max = Math.max(...points.map(point => point.total_volume), 1);
  const step = plotWidth / points.length;
  const y = (value: number) => top + plotHeight * (1 - value / max);
  const x = (index: number) => left + step * (index + .5);
  const line = points.map((point, index) => `${x(index)},${y(point.total_volume)}`).join(" ");
  const selected = active === null ? null : points[active];
  const date = (value: string) => new Date(value).toLocaleString("en-GB", { timeZone: "UTC", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
  return <figure className="activity-chart">
    <figcaption><h2>Activity over time</h2><p className="muted">UTC calendar buckets. Dark line: total posts. Bars: sentiment composition.</p></figcaption>
    <div className="chart-legend"><span className="positive">Positive</span><span>Neutral</span><span className="negative">Negative</span></div>
    <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Post activity with positive, neutral and negative composition over time. Exact values are in the table below.">
      <title>Activity over time</title>
      {[0, max / 2, max].map(value => <g key={value}><line x1={left} x2={width - 12} y1={y(value)} y2={y(value)} stroke="var(--border-structural)" /><text x={left - 6} y={y(value) + 4} textAnchor="end">{Math.round(value)}</text></g>)}
      {points.map((point, index) => {
        const bar = Math.max(step * .7, 1);
        const values = [point.positive_count, point.neutral_count, point.negative_count];
        const colors = ["var(--sentiment-pos)", "var(--sentiment-neu)", "var(--sentiment-neg)"];
        let sum = 0;
        return <g key={point.window_start} tabIndex={0} onMouseEnter={() => setActive(index)} onFocus={() => setActive(index)} aria-label={`${date(point.window_start)} UTC: ${point.total_volume} posts, ${values[0]} positive, ${values[1]} neutral, ${values[2]} negative`}>
          <rect x={x(index) - step / 2} y={top} width={step} height={plotHeight} fill="transparent" />
          {values.map((value, segment) => { sum += value; return <rect key={segment} x={x(index) - bar / 2} y={y(sum)} width={bar} height={plotHeight * value / max} fill={colors[segment]} />; })}
          <title>{date(point.window_start)} UTC · {point.total_volume} posts · {point.positive_count} positive / {point.neutral_count} neutral / {point.negative_count} negative</title>
        </g>;
      })}
      <polyline points={line} fill="none" stroke="var(--text-primary)" strokeWidth={2} pointerEvents="none" />
      {[0, Math.floor((points.length - 1) / 2), points.length - 1].filter((value, index, all) => all.indexOf(value) === index).map(index => <text key={index} x={x(index)} y={height - 9} textAnchor={index === 0 ? "start" : index === points.length - 1 ? "end" : "middle"}>{date(points[index].window_start)}</text>)}
    </svg>
    <output className="numeric chart-readout" aria-live="polite">{selected ? `${date(selected.window_start)} UTC · ${selected.total_volume} posts · ${selected.positive_count} positive · ${selected.neutral_count} neutral · ${selected.negative_count} negative` : "Hover or focus a time bucket for exact values."}</output>
    <details><summary>View activity data table</summary><div className="table-wrap"><table><caption className="sr-only">Activity by UTC time bucket</caption><thead><tr><th scope="col">UTC bucket</th><th scope="col">Posts</th><th scope="col">Positive</th><th scope="col">Neutral</th><th scope="col">Negative</th><th scope="col">Avg. engagement</th></tr></thead><tbody>{points.map(point => <tr key={point.window_start}><th scope="row">{date(point.window_start)}</th><td className="numeric">{point.total_volume}</td><td className="numeric">{point.positive_count}</td><td className="numeric">{point.neutral_count}</td><td className="numeric">{point.negative_count}</td><td className="numeric">{point.avg_engagement}</td></tr>)}</tbody></table></div></details>
  </figure>;
}
export function Sparkline({ values }: { values: number[] }) {
  if (!values.length) return <span>—</span>;
  const max = Math.max(...values, 1);
  return <svg className="sparkline" viewBox="0 0 88 24" role="img" aria-label={`Activity: ${values.join(", ")} posts`}><polyline fill="none" stroke="currentColor" strokeWidth="1.5" points={values.map((value, index) => `${index * 84 / Math.max(values.length - 1, 1) + 2},${22 - value / max * 20}`).join(" ")} /></svg>;
}
