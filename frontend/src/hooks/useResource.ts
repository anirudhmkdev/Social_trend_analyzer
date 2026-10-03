"use client";
import { useEffect, useState } from "react";

export function useResource<T>(key: string, request: () => Promise<T>, enabled = true) {
  const [data, setData] = useState<T | null>(null), [error, setError] = useState("");
  const [loading, setLoading] = useState(enabled), [revision, setRevision] = useState(0);
  useEffect(() => {
    let canceled = false;
    setData(null); setError(""); setLoading(enabled);
    if (enabled) request().then(result => { if (!canceled) setData(result); })
      .catch(err => { if (!canceled) setError(err.message); })
      .finally(() => { if (!canceled) setLoading(false); });
    return () => { canceled = true; };
    // Callers supply a complete resource identity (including all filters).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, enabled, revision]);
  return { data, error, loading, retry: () => setRevision(value => value + 1) };
}
