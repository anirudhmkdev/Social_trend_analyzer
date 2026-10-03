/** Parallel contracts for the Pydantic v1 API. Integration tests check real responses. */
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
export type WindowSize = "hourly" | "daily" | "weekly";
export type Classification = "emerging" | "rising" | "stable" | "declining";
export type Sentiment = "positive" | "neutral" | "negative";
export type ColumnField = "text" | "timestamp" | "platform" | "hashtags" | "likes" | "comments" | "shares" | "author_id" | "external_id";
export type ColumnMapping = Record<ColumnField, string | null>;
export interface ValidationResult {
  total_rows: number; valid_rows: number; invalid_rows: number;
  issues: { missing_text: number; missing_timestamp: number; invalid_timestamp: number; duplicate_posts: number };
  date_range: { earliest: string | null; latest: string | null };
  platform_distribution: Record<string, number>; missing_field_counts: Record<string, number>;
  row_issues: Array<{ row_index: number; issue_type: string; detail: string }>;
  issues_truncated: boolean;
}
export interface DatasetItem {
  id: string; name: string; filename: string; source_type: string;
  row_count: number | null; valid_row_count: number | null; status: string;
  column_mapping: ColumnMapping | null; validation_results: ValidationResult | null;
  upload_metadata: { encoding: string; warnings: string[]; ambiguous_fields: string[] } | null;
  created_at: string; updated_at: string;
}
export interface DatasetListResponse { datasets: DatasetItem[]; total: number }
export interface DatasetPreview {
  dataset_id: string; columns: string[]; rows: Array<Record<string, unknown>>;
  total_rows: number; shown_rows: number; kind: "raw" | "normalized"; warnings: string[];
  detection: null | { available_columns: string[]; ambiguous_fields: string[];
    detected: Record<ColumnField, { source_column: string | null; confidence: number }> };
}
export interface AnalysisRun {
  id: string; dataset_id: string; status: "pending" | "running" | "completed" | "failed";
  progress_pct: number; current_step: string | null; error_message: string | null;
  created_at: string; started_at: string | null; completed_at: string | null;
  config: Record<string, unknown>; model_info: Record<string, unknown> | null; stats: Record<string, unknown> | null;
}
export interface TrendSnapshot {
  id: string; analysis_run_id: string; topic_id: string; topic_name: string | null;
  time_window: string; window_start: string; window_end: string;
  trend_score: number; classification: Classification; explanation: string;
  volume_current: number; volume_previous: number; volume_growth_pct: number | null;
  engagement_current: number | null; engagement_previous: number | null; engagement_growth_pct: number | null;
  velocity: number | null; burst_score: number | null; recency_score: number | null;
  sentiment_positive_pct: number | null; sentiment_neutral_pct: number | null; sentiment_negative_pct: number | null;
  activity: number[]; min_posts_for_trend: number;
}
export interface TimelinePoint {
  window_start: string; window_end: string; total_volume: number;
  positive_count: number; neutral_count: number; negative_count: number; avg_engagement: number;
}
export interface TimelineResponse { time_window: string; timeline: TimelinePoint[]; total_points: number }
export interface EntityItem { text: string; label: string; frequency: number }
export interface KeywordItem { keyword: string; frequency: number; tfidf_score?: number | null; growth_rate?: number | null }
export interface DashboardSummary {
  analysis_run_id: string | null; dataset_id: string | null; dataset_name: string | null; status: string;
  total_posts: number; total_topics: number;
  sentiment_breakdown: { counts: Record<Sentiment, number>; percentages: Record<Sentiment, number>; total: number };
  trend_classifications: Record<Classification, number>; top_trends: TrendSnapshot[];
  top_entities: EntityItem[]; top_hashtags: KeywordItem[]; top_keywords: KeywordItem[];
  platform_breakdown: Record<string, number>; model_info: Record<string, unknown>;
}
export interface TopicItem {
  id: string; analysis_run_id: string; topic_index: number; display_name: string;
  keywords: Array<{ word: string; score: number }>; representative_docs: string[] | null;
  model_metadata: Record<string, unknown> | null; post_count: number; is_outlier: boolean;
  latest_trend: TrendSnapshot | null;
}
export interface PostItem {
  id: string; dataset_id: string; original_text: string; cleaned_text?: string | null;
  timestamp: string; platform: string | null; likes: number | null; comments: number | null; shares: number | null;
  hashtags?: string[] | null; sentiment: Sentiment | null; topic_name?: string | null; probability?: number | null;
}
export interface PostSearchResponse { items: PostItem[]; total: number; limit: number; offset: number }
export interface TopicDetailResponse {
  topic: TopicItem; dataset_id: string; sentiment_distribution: Record<Sentiment, number>;
  avg_engagement: Record<"likes" | "comments" | "shares", number | null>; sample_posts: PostItem[];
  entities: EntityItem[]; keywords: KeywordItem[]; hashtags: KeywordItem[];
  trend_history: TrendSnapshot[]; timeline: TimelinePoint[];
}
export interface PipelineMetadata {
  preprocessing_version: string; embedding_model: string; embedding_dimensions: number;
  sentiment_model: string; sentiment_license: string; ner_model: string; topic_model: string;
  trend_weights: Record<string, number>; trend_thresholds: Record<string, number>; min_posts_for_trend: number;
  active_run: { id: string; dataset_id: string; status: string; current_step: string; progress_pct: number } | null;
  database_backend: string; package_versions: Record<string, string>; run_model_info: Record<string, unknown>;
  run_stats: Record<string, unknown>; ner_status: { model?: string; status?: string; warning?: string | null };
}
export class ApiError extends Error {
  constructor(public status: number, message: string, public data?: unknown) { super(message); this.name = "ApiError"; }
}
function serverError(data: unknown): string | undefined {
  if (!data || typeof data !== "object") return;
  if ("error" in data && typeof data.error === "string") return data.error;
  if ("detail" in data) {
    if (typeof data.detail === "string") return data.detail;
    if (Array.isArray(data.detail)) return data.detail.map(item => item.msg || "Invalid input").join("; ");
  }
}
export async function fetchJson<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL.replace(/\/+$/, "")}/${endpoint.replace(/^\/+/, "")}`, {
      ...options, headers: { ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }), ...options.headers },
      signal: options.signal || AbortSignal.timeout(30000),
    });
  } catch {
    throw new ApiError(0, "API unavailable. Start the backend, check its address, and try again.");
  }
  if (!response.ok) {
    const data: unknown = await response.json().catch(() => null);
    throw new ApiError(response.status, serverError(data) || `Request failed (${response.status}). Try again.`, data);
  }
  if (response.status === 204) return undefined as T;
  return response.json();
}
function params(values: object): string {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(values)) if (value !== undefined && value !== "") query.set(key, String(value));
  return query.toString();
}
export interface ReadContext { dataset_id?: string; analysis_run_id?: string; time_window?: WindowSize; platform?: string }
export const api = {
  getHealth: () => fetchJson<{ status: string }>("/health"),
  getDatasets: (offset = 0) => fetchJson<DatasetListResponse>(`/datasets?limit=200&offset=${offset}`),
  getDataset: (id: string) => fetchJson<DatasetItem>(`/datasets/${id}`),
  uploadDataset: (file: File) => { const body = new FormData(); body.set("file", file); return fetchJson<DatasetItem>("/datasets/upload", { method: "POST", body }); },
  getPreview: (id: string) => fetchJson<DatasetPreview>(`/datasets/${id}/preview`),
  mapColumns: (id: string, mapping: ColumnMapping) => fetchJson<DatasetItem>(`/datasets/${id}/map-columns`, { method: "POST", body: JSON.stringify(mapping) }),
  validateDataset: (id: string) => fetchJson<ValidationResult>(`/datasets/${id}/validate`, { method: "POST" }),
  importDataset: (id: string) => fetchJson<DatasetItem>(`/datasets/${id}/import`, { method: "POST" }),
  deleteDataset: (id: string) => fetchJson<void>(`/datasets/${id}`, { method: "DELETE" }),
  loadSampleDataset: () => fetchJson<{ dataset_id: string; row_count: number; name: string; message: string }>("/datasets/sample", { method: "POST" }),
  getAnalysisRuns: (id: string) => fetchJson<{ runs: AnalysisRun[]; total: number }>(`/analysis?dataset_id=${id}`),
  triggerAnalysisRun: (id: string) => fetchJson<AnalysisRun>("/analysis/run", { method: "POST", body: JSON.stringify({ dataset_id: id }) }),
  getAnalysisRunStatus: (id: string) => fetchJson<AnalysisRun>(`/analysis/${id}/status`),
  getDashboardSummary: (context: ReadContext) => fetchJson<DashboardSummary>(`/dashboard/summary?${params(context)}`),
  getTimeline: (context: ReadContext, topicId?: string) => fetchJson<TimelineResponse>(`/dashboard/timeline?${params({ ...context, topic_id: topicId })}`),
  getTopics: (context: ReadContext, classification?: string, q?: string) => fetchJson<{ topics: TopicItem[]; total_topics: number; outlier_count: number }>(`/topics?${params({ ...context, classification, q })}`),
  getTopicDetail: (id: string, runId?: string, context: ReadContext = {}) => fetchJson<TopicDetailResponse>(`/topics/${id}?${params({ ...context, analysis_run_id: runId })}`),
  searchPosts: (query: ReadContext & { q?: string; sentiment?: string; topic_id?: string; date_from?: string; date_to?: string; limit?: number; offset?: number }) => fetchJson<PostSearchResponse>(`/posts/search?${params(query)}`),
  getPipelineMetadata: (runId?: string) => fetchJson<PipelineMetadata>(`/pipeline/metadata?${params({ analysis_run_id: runId })}`),
};
