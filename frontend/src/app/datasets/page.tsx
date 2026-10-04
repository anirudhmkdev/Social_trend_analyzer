"use client";
import { FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAnalysis } from "@/components/AnalysisContext";
import { ErrorNotice, Loading } from "@/components/Feedback";
import { DeleteDataset } from "@/components/DeleteDataset";

export default function DatasetsPage() {
  const ctx = useAnalysis(), router = useRouter();
  const [adding, setAdding] = useState(false), [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false), [error, setError] = useState("");
  async function upload(event: FormEvent) { event.preventDefault(); if (!file) return; setBusy(true); setError(""); try { const dataset = await api.uploadDataset(file); ctx.refresh(); router.push(`/datasets/${dataset.id}`); } catch (err) { setError(err instanceof Error ? err.message : "Upload failed."); } finally { setBusy(false); } }
  async function demo() { setBusy(true); setError(""); try { const result = await api.loadSampleDataset(); ctx.refresh(); router.push(`/datasets/${result.dataset_id}`); } catch (err) { setError(err instanceof Error ? err.message : "Demo could not be loaded."); } finally { setBusy(false); } }
  return <div className="page"><div className="page-heading"><div><h1>Datasets</h1><p>Upload once. Review the source, map columns and import valid posts before analysis.</p></div><div className="actions"><button className="primary" onClick={() => setAdding(!adding)} aria-expanded={adding}>Add Dataset</button><button disabled={busy} onClick={demo}>Use Demo Dataset</button></div></div>
    <ErrorNotice error={error || ctx.error} retry={ctx.refresh} />
    {adding && <section className="panel"><div className="panel-heading"><h2>Upload CSV</h2></div><form className="panel-body page" onSubmit={upload}><label>CSV file<input type="file" accept=".csv,text/csv" required onChange={event => setFile(event.target.files?.[0] || null)} /></label><p className="muted">UTF-8 or Windows-1252 CSV, up to 50 MB. Text and timestamp columns are required; other fields are optional. English text is supported by the configured models.</p><div className="actions"><button className="primary" disabled={busy || !file}>{busy ? "Uploading…" : "Upload and preview"}</button><button type="button" onClick={() => setAdding(false)}>Cancel</button></div></form></section>}
    <section className="panel"><div className="panel-heading"><h2>Dataset repository</h2><span className="numeric">{ctx.datasets.length} datasets</span></div>{ctx.loading ? <Loading text="Loading datasets…" /> : !ctx.datasets.length ? <div className="empty-state"><h2>Your first dataset</h2><p>Choose Add Dataset to upload your own CSV. The 900-post demo is available for a reproducible walkthrough.</p><button onClick={() => setAdding(true)}>Add Dataset</button></div> : <div className="table-wrap"><table><thead><tr>{["Dataset", "Source", "Rows", "Import status", "Created", "Actions"].map(name => <th scope="col" key={name}>{name}</th>)}</tr></thead><tbody>{ctx.datasets.map(dataset => <tr key={dataset.id}><th scope="row"><Link href={`/datasets/${dataset.id}`}>{dataset.name}</Link><div className="muted">{dataset.filename}</div></th><td>{dataset.source_type === "synthetic_demo" ? "Synthetic demo" : "CSV upload"}</td><td className="numeric">{dataset.valid_row_count ?? dataset.row_count ?? "—"}</td><td>{dataset.status}</td><td><time dateTime={dataset.created_at}>{new Date(dataset.created_at).toLocaleDateString()}</time></td><td><div className="actions"><Link className="button" href={`/datasets/${dataset.id}`}>{["imported", "preprocessed"].includes(dataset.status) ? "Analysis & history" : "Continue import"}</Link><DeleteDataset id={dataset.id} name={dataset.name} onDeleted={() => { ctx.select({ dataset: undefined, run: undefined }); ctx.refresh(); }} /></div></td></tr>)}</tbody></table></div>}</section>
  </div>;
}
