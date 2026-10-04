"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { api, AnalysisRun, DatasetItem, ReadContext, WindowSize } from "@/lib/api";

interface ContextState {
  datasets: DatasetItem[]; dataset?: DatasetItem; runs: AnalysisRun[]; run?: AnalysisRun;
  loading: boolean; error: string; timeWindow: WindowSize; platform: string;
  read: ReadContext; query: string;
  select: (values: Record<string, string | undefined>) => void; refresh: () => void;
}
const Context = createContext<ContextState | null>(null);
export function AnalysisProvider({ children }: { children: ReactNode }) {
  const router = useRouter(), pathname = usePathname(), search = useSearchParams();
  const routeDatasetId = pathname.startsWith("/datasets/") ? pathname.split("/")[2] : null;
  const datasetId = routeDatasetId || search.get("dataset"), runId = search.get("run");
  const [datasets, setDatasets] = useState<DatasetItem[]>([]);
  const [runs, setRuns] = useState<AnalysisRun[]>([]);
  const [loadingDatasets, setLoadingDatasets] = useState(true), [loadingRuns, setLoadingRuns] = useState(false);
  const [error, setError] = useState("");
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    let canceled = false;
    setLoadingDatasets(true); setError("");
    (async () => {
      const first = await api.getDatasets();
      const all = [...first.datasets];
      for (let offset = all.length; offset < first.total; offset += 200) all.push(...(await api.getDatasets(offset)).datasets);
      if (!canceled) setDatasets(all);
    })().catch(err => { if (!canceled) setError(err.message); }).finally(() => { if (!canceled) setLoadingDatasets(false); });
    return () => { canceled = true; };
  }, [revision]);
  const dataset = datasetId ? datasets.find(item => item.id === datasetId) : datasets[0];
  const selectedId = dataset?.id;
  useEffect(() => {
    let canceled = false;
    setRuns([]);
    if (!selectedId) { setLoadingRuns(false); return; }
    setLoadingRuns(true);
    api.getAnalysisRuns(selectedId).then(result => { if (!canceled) setRuns(result.runs); })
      .catch(err => { if (!canceled) setError(err.message); })
      .finally(() => { if (!canceled) setLoadingRuns(false); });
    return () => { canceled = true; };
  }, [selectedId, revision]);
  const scopedRuns = runs.filter(item => item.dataset_id === selectedId);
  const run = runId ? scopedRuns.find(item => item.id === runId)
    : scopedRuns.find(item => item.status === "completed") || scopedRuns[0];
  const loading = loadingDatasets || loadingRuns;
  const contextError = error || (!loading && datasetId && !dataset ? "This dataset is unavailable or was deleted. Choose another dataset." : "")
    || (!loading && runId && dataset && !run ? "This analysis run is unavailable or belongs to another dataset. Choose a run from this dataset." : "");
  function select(values: Record<string, string | undefined>) {
    const next = new URLSearchParams(search.toString());
    for (const [key, value] of Object.entries(values)) { if (value) next.set(key, value); else next.delete(key); }
    router.replace(`${pathname}${next.size ? `?${next}` : ""}`, { scroll: false });
  }
  useEffect(() => {
    if (loading || contextError || !dataset || pathname.startsWith("/datasets")) return;
    const next = new URLSearchParams(search.toString());
    let changed = false;
    if (!datasetId) { next.set("dataset", dataset.id); changed = true; }
    if (!runId && run) { next.set("run", run.id); changed = true; }
    if (changed) router.replace(`${pathname}?${next}`, { scroll: false });
  }, [loading, contextError, dataset, run, datasetId, runId, search, pathname, router]);
  useEffect(() => {
    if (!run || !["pending", "running"].includes(run.status)) return;
    let canceled = false;
    const timer = setInterval(() => api.getAnalysisRunStatus(run.id).then(status => {
      if (!canceled) setRuns(current => current.map(item => item.id === status.id ? status : item));
    }).catch(err => { if (!canceled) setError(err.message); }), 2000);
    return () => { canceled = true; clearInterval(timer); };
  }, [run]);
  const windowValue = search.get("window");
  const timeWindow: WindowSize = windowValue === "hourly" || windowValue === "weekly" ? windowValue : "daily";
  const platform = search.get("platform") || "";
  const canonical = new URLSearchParams();
  if (dataset) canonical.set("dataset", dataset.id);
  if (run) canonical.set("run", run.id);
  canonical.set("window", timeWindow);
  if (platform) canonical.set("platform", platform);
  return <Context.Provider value={{ datasets, dataset, runs: scopedRuns, run, loading, error: contextError,
    timeWindow, platform, select, refresh: () => setRevision(value => value + 1), query: canonical.toString(),
    read: { dataset_id: dataset?.id, analysis_run_id: run?.id, time_window: timeWindow, platform: platform || undefined } }}>
    {children}
  </Context.Provider>;
}
export function useAnalysis() { const value = useContext(Context); if (!value) throw new Error("AnalysisProvider missing"); return value; }
export function ContextToolbar({ filters = true }: { filters?: boolean }) {
  const ctx = useAnalysis();
  const platforms = Object.keys(ctx.dataset?.validation_results?.platform_distribution || {});
  return <section className="context-toolbar" aria-label="Analysis context">
    <label>Dataset<select value={ctx.dataset?.id || ""} disabled={ctx.loading} onChange={event => ctx.select({ dataset: event.target.value, run: undefined, platform: undefined, topic: undefined })}>
      {!ctx.dataset && <option value="">Choose a dataset</option>}{ctx.datasets.map(dataset => <option key={dataset.id} value={dataset.id}>{dataset.name}</option>)}
    </select></label>
    <label>Analysis run<select value={ctx.run?.id || ""} disabled={ctx.loading || !ctx.dataset} onChange={event => ctx.select({ run: event.target.value, topic: undefined })}>
      {!ctx.run && <option value="">No analysis runs</option>}{ctx.runs.map(run => <option key={run.id} value={run.id}>{new Date(run.created_at).toLocaleString()} · {run.status} · {run.id.slice(0, 8)}</option>)}
    </select></label>
    {filters && <><label>Time window<select value={ctx.timeWindow} onChange={event => ctx.select({ window: event.target.value })}>
      <option value="hourly">Hourly</option><option value="daily">Daily</option><option value="weekly">Weekly</option>
    </select></label><label>Platform<select value={ctx.platform} onChange={event => ctx.select({ platform: event.target.value })}>
      <option value="">All platforms</option>{platforms.map(platform => <option key={platform}>{platform}</option>)}
    </select></label></>}
  </section>;
}
export function AnalysisState() {
  const ctx = useAnalysis();
  if (ctx.loading) return <p role="status" className="empty-state">Loading dataset and analysis context…</p>;
  if (ctx.error) return <div role="alert" className="notice error"><p>{ctx.error}</p><button onClick={ctx.refresh}>Retry</button> <button onClick={() => ctx.select({ dataset: undefined, run: undefined })}>Reset selection</button></div>;
  if (!ctx.dataset) return <div className="empty-state"><h2>Start with a dataset</h2><p>Upload a CSV, map its fields and run local NLP analysis.</p><Link className="button primary" href="/datasets">Add Dataset</Link></div>;
  if (!ctx.run) return <div className="empty-state"><h2>{["imported", "preprocessed"].includes(ctx.dataset.status) ? "Ready for analysis" : "Finish importing this dataset"}</h2><p>No analysis has been run for this dataset.</p><Link className="button primary" href={`/datasets/${ctx.dataset.id}`}>Open dataset</Link></div>;
  if (ctx.run.status === "failed") return <div role="alert" className="notice error"><h2>Analysis failed</h2><p>{ctx.run.error_message}</p><Link className="button" href={`/datasets/${ctx.dataset.id}`}>Review and retry analysis</Link></div>;
  if (ctx.run.status !== "completed") return <div className="empty-state" role="status"><h2>Analysis {ctx.run.status}</h2><p>{ctx.run.current_step}</p><progress max={100} value={ctx.run.progress_pct} aria-label="Analysis progress" /><p className="numeric">{ctx.run.progress_pct}% complete</p><Link href={`/datasets/${ctx.dataset.id}`}>View analysis history</Link></div>;
  return null;
}
export function ModelWarning() {
  const ctx = useAnalysis();
  const info = ctx.run?.model_info;
  if (info?.legacy_unverified) return <div className="notice" role="status">This historical analysis has unverified model provenance. Run analysis again to establish actual model and enrichment status. <Link href={`/datasets/${ctx.dataset?.id}`}>Open analysis history</Link></div>;
  return info?.degraded ? <div className="notice" role="status">Completed with limited enrichment. {Array.isArray(info.warnings) ? info.warnings.filter(value => typeof value === "string").join(" ") : ""} <Link href={`/analysis?${ctx.query}`}>Inspect model status</Link></div> : null;
}
