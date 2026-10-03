export function ErrorNotice({ error, retry }: { error: string; retry?: () => void }) {
  if (!error) return null;
  return <div className="notice error" role="alert"><p>{error}</p>{retry && <button onClick={retry}>Try again</button>}</div>;
}
export function Loading({ text = "Loading results…" }: { text?: string }) { return <p className="loading" role="status">{text}</p>; }
