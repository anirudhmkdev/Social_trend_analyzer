"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api, AnalysisRun, ColumnField, ColumnMapping } from "@/lib/api";
import { useResource } from "@/hooks/useResource";
import { useAnalysis } from "@/components/AnalysisContext";
import { ErrorNotice, Loading } from "@/components/Feedback";
import { DeleteDataset } from "@/components/DeleteDataset";

const fields: ColumnField[] = ["text", "timestamp", "platform", "hashtags", "likes", "comments", "shares", "author_id", "external_id"];
const emptyMapping: ColumnMapping = { text: null, timestamp: null, platform: null, hashtags: null, likes: null, comments: null, shares: null, author_id: null, external_id: null };
export default function DatasetDetailPage() {
  const { id } = useParams<{ id: string }>(), router = useRouter(), ctx = useAnalysis();
  const resource = useResource(id, () => Promise.all([api.getDataset(id), api.getPreview(id), api.getAnalysisRuns(id)]));
  const [mapping, setMapping] = useState<ColumnMapping>(emptyMapping), [busy, setBusy] = useState(false), [error, setError] = useState("");
  const [confirmed, setConfirmed] = useState(false), [active, setActive] = useState<AnalysisRun | null>(null);
  const dataset = resource.data?.[0], preview = resource.data?.[1], runs = resource.data?.[2].runs || [];
  useEffect(() => { if (dataset) setMapping({ ...emptyMapping, ...dataset.column_mapping }); }, [dataset]);
  useEffect(() => { setActive(runs.find(run => ["pending", "running"].includes(run.status)) || null); }, [resource.data]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (!active || !["pending", "running"].includes(active.status)) return;
    let canceled = false;
    const timer = setInterval(() => api.getAnalysisRunStatus(active.id).then(run => {
      if (canceled) return; setActive(run);
      if (["completed", "failed"].includes(run.status)) { resource.retry(); ctx.refresh(); }
    }).catch(err => { if (!canceled) setError(err.message); }), 2000);
    return () => { canceled = true; clearInterval(timer); };
  }, [active]); // eslint-disable-line react-hooks/exhaustive-deps
  async function action(task: () => Promise<unknown>) { setBusy(true); setError(""); try { await task(); resource.retry(); ctx.refresh(); setConfirmed(false); } catch (err) { setError(err instanceof Error ? err.message : "Request failed. Try again."); } finally { setBusy(false); } }
  if (resource.loading) return <Loading text="Loading dataset, source preview and analysis history…" />;
  if (!dataset || !preview) return <><ErrorNotice error={resource.error || "Dataset unavailable."} retry={resource.retry} /><Link href="/datasets">Return to Datasets to upload the source again or select another dataset.</Link></>;
  const imported = ["imported", "preprocessed"].includes(dataset.status);
  const dirty = JSON.stringify(mapping) !== JSON.stringify({ ...emptyMapping, ...dataset.column_mapping });
  const validation = dataset.validation_results;
  return <div className="page"><div className="page-heading"><div><Link href="/datasets">Datasets</Link><h1>{dataset.name}</h1><p>{dataset.filename} · {dataset.row_count} source rows · {dataset.status}</p></div><DeleteDataset id={id} name={dataset.name} onDeleted={() => { ctx.refresh(); router.push("/datasets"); }} /></div><ErrorNotice error={error || resource.error} retry={resource.retry} />
    {!imported && <section className="panel"><div className="panel-heading"><h2>Column mapping</h2><span className="muted">Required: text and timestamp</span></div><div className="panel-body">
      {!!preview.detection?.ambiguous_fields.length && <p className="notice">Multiple possible columns: {preview.detection.ambiguous_fields.join(", ")}. Review the suggested mapping before continuing.</p>}
      <div className="mapping-grid">{fields.map(field => <label key={field}>{field === "text" ? "Text column *" : field === "timestamp" ? "Timestamp column *" : field.replace("_", " ")}<select value={mapping[field] || ""} onChange={event => setMapping(current => ({ ...current, [field]: event.target.value || null }))}><option value="">{["text", "timestamp"].includes(field) ? "Choose a column" : "Not available"}</option>{preview.columns.map(column => <option key={column}>{column}</option>)}</select>{preview.detection?.detected[field]?.source_column && <small className="muted">Auto-detected: {preview.detection.detected[field].source_column}</small>}</label>)}</div>
      <div className="actions"><button disabled={busy || !mapping.text || !mapping.timestamp} onClick={() => action(() => api.mapColumns(id, mapping))}>Confirm mapping</button><button disabled={busy || dirty || !["mapped", "validated"].includes(dataset.status)} onClick={() => action(() => api.validateDataset(id))}>Validate CSV</button></div>{dirty && <p className="muted">Mapping changed. Confirm it before validation.</p>}
    </div></section>}
    {validation && <section className="panel"><div className="panel-heading"><h2>Validation summary</h2></div><div className="panel-body page"><p className="numeric">{validation.valid_rows} valid · {validation.invalid_rows} invalid · {validation.issues.duplicate_posts} duplicates retained and flagged</p><p className="muted">Invalid rows are excluded from import. Repeated text is retained because posts may recur over time; each repeated text is flagged. Row indices below are zero-based source data rows (header excluded).</p><div className="table-wrap"><table><thead><tr><th scope="col">Source row index</th><th scope="col">Issue</th><th scope="col">Details</th></tr></thead><tbody>{validation.row_issues.map((issue, index) => <tr key={index}><td className="numeric">{issue.row_index}</td><td>{issue.issue_type}</td><td>{issue.detail}</td></tr>)}{!validation.row_issues.length && <tr><td colSpan={3}>No row problems found.</td></tr>}</tbody></table></div>{validation.issues_truncated && <p>Showing the first 200 issues. Correct the source file before uploading again if you need to review every invalid row.</p>}
      {!imported && <><label className="checkbox-label"><input type="checkbox" checked={confirmed} onChange={event => setConfirmed(event.target.checked)} />Import the valid rows; retain and flag duplicate text.</label><button className="primary" disabled={busy || dirty || !confirmed || validation.valid_rows === 0} onClick={() => action(() => api.importDataset(id))}>Import valid rows</button>{validation.valid_rows === 0 && <p role="alert">No valid rows. Correct the mapping, or upload a corrected CSV.</p>}</>}
    </div></section>}
    <section className="panel"><div className="panel-heading"><h2>{preview.kind === "raw" ? "Raw CSV preview" : "Imported posts preview"}</h2><span className="numeric">{preview.shown_rows} / {preview.total_rows}</span></div><div className="table-wrap"><table className="raw-table"><thead><tr>{preview.columns.map(column => <th scope="col" key={column}>{column}</th>)}</tr></thead><tbody>{preview.rows.map((row, index) => <tr key={index}>{preview.columns.map(column => <td key={column}>{row[column] === null || row[column] === undefined ? "—" : typeof row[column] === "object" ? JSON.stringify(row[column]) : String(row[column])}</td>)}</tr>)}</tbody></table></div></section>
    <section className="panel"><div className="panel-heading"><h2>Analysis history</h2><button className="primary" disabled={!imported || busy || !!active && ["pending", "running"].includes(active.status)} onClick={() => action(async () => { const run = await api.triggerAnalysisRun(id); setActive(run); })}>Run Analysis</button></div>{!imported && <p className="panel-body">Import valid rows before running the pipeline.</p>}{active && <div className="panel-body" role="status"><p>{active.status} · {active.current_step}</p><progress max={100} value={active.progress_pct} aria-label="Analysis progress" /><span className="numeric"> {active.progress_pct}%</span>{active.error_message && <p role="alert">{active.error_message}</p>}</div>}<div className="table-wrap"><table><thead><tr><th scope="col">Run</th><th scope="col">Created</th><th scope="col">Status</th><th scope="col">Result</th></tr></thead><tbody>{runs.map(run => <tr key={run.id}><td className="numeric">{run.id.slice(0, 8)}</td><td><time>{new Date(run.created_at).toLocaleString()}</time></td><td>{run.status}<div className="muted">{run.current_step}</div></td><td>{run.status === "completed" ? <Link className="button" href={`/dashboard?dataset=${id}&run=${run.id}`}>Open Dashboard</Link> : run.status === "failed" ? <span className="negative">{run.error_message}</span> : <span className="numeric">{run.progress_pct}%</span>}</td></tr>)}{!runs.length && <tr><td colSpan={4}>No analysis runs yet.</td></tr>}</tbody></table></div></section>
  </div>;
}
