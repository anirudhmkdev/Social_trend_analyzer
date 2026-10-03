"use client";
import { useId, useRef, useState } from "react";
import { api } from "@/lib/api";
import { ErrorNotice } from "./Feedback";

export function DeleteDataset({ id, name, onDeleted }: { id: string; name: string; onDeleted: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null), title = useId();
  const [busy, setBusy] = useState(false), [error, setError] = useState("");
  async function remove() { setBusy(true); setError(""); try { await api.deleteDataset(id); dialog.current?.close(); onDeleted(); } catch (err) { setError(err instanceof Error ? err.message : "Deletion failed. Try again."); } finally { setBusy(false); } }
  return <><button className="destructive" onClick={() => { setError(""); dialog.current?.showModal(); }}>Delete dataset</button><dialog ref={dialog} aria-labelledby={title}><h2 id={title}>Delete this dataset?</h2><p>{name}</p><p>Its uploaded file, posts, analysis runs and results will be permanently removed.</p><ErrorNotice error={error} /><div className="actions"><button autoFocus disabled={busy} onClick={() => dialog.current?.close()}>Cancel</button><button className="destructive" disabled={busy} onClick={remove}>{busy ? "Deleting…" : "Confirm deletion"}</button></div></dialog></>;
}
