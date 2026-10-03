/**
 * Social Trend Analyzer — Typed API Client
 */

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export interface HealthCheckResponse {
  status: string;
}

export interface TrendSnapshot {
  id: string;
  topic_id: string;
  topic_name?: string;
  time_window: string;
  window_start: string;
  window_end: string;
  trend_score: number;
  classification: "emerging" | "rising" | "stable" | "declining";
  explanation: string;
  volume_current: number;
  volume_previous: number;
  volume_growth_pct?: number;
  engagement_current?: number;
  engagement_previous?: number;
  engagement_growth_pct?: number;
  velocity?: number;
  burst_score?: number;
  recency_score?: number;
  sentiment_positive_pct?: number;
  sentiment_neutral_pct?: number;
  sentiment_negative_pct?: number;
}

export interface DashboardSummary {
  analysis_run_id?: string;
  dataset_id?: string;
  dataset_name?: string;
  status: string;
  total_posts: number;
  total_topics: number;
  sentiment_breakdown: {
    counts: { positive: number; neutral: number; negative: number };
    percentages: { positive: number; neutral: number; negative: number };
    total: number;
  };
  trend_classifications: {
    emerging: number;
    rising: number;
    stable: number;
    declining: number;
  };
  top_trends: TrendSnapshot[];
  top_entities: Array<{ text: string; label: string; frequency: number }>;
  top_hashtags: Array<{ keyword: string; frequency: number; growth_rate?: number }>;
  top_keywords: Array<{ keyword: string; frequency: number; tfidf_score: number }>;
  platform_breakdown: Record<string, number>;
  model_info: Record<string, unknown>;
}

export interface TimelinePoint {
  window_start: string;
  window_end: string;
  total_volume: number;
  positive_count: number;
  neutral_count: number;
  negative_count: number;
  avg_engagement: number;
}

export interface TimelineResponse {
  time_window: string;
  timeline: TimelinePoint[];
  total_points: number;
}

export interface TopicItem {
  id: string;
  topic_index: number;
  display_name: string;
  keywords: Array<{ word: string; score: number }>;
  representative_docs: string[];
  post_count: number;
  is_outlier: boolean;
  sentiment_distribution?: Record<string, number>;
  avg_engagement?: number;
  trend_score?: number;
  trend_classification?: string;
}

export interface TopicDetailResponse {
  topic: TopicItem;
  sentiment_distribution: Record<string, number>;
  avg_engagement: number;
  sample_posts: Array<{
    id: string;
    text: string;
    timestamp: string;
    platform?: string;
    likes?: number;
  }>;
}

export interface DatasetItem {
  id: string;
  name: string;
  filename: string;
  source_type: string;
  row_count?: number;
  valid_row_count?: number;
  status: string;
  created_at: string;
  latest_run?: {
    id: string;
    status: string;
    completed_at?: string;
  };
}

export interface PostItem {
  id: string;
  dataset_id: string;
  original_text: string;
  cleaned_text?: string;
  sentiment_ready_text?: string;
  timestamp: string;
  platform?: string;
  author_id?: string;
  likes?: number;
  comments?: number;
  shares?: number;
  hashtags?: string[];
  sentiment?: string;
  topic_name?: string;
}

export interface PostSearchResponse {
  items: PostItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface PipelineMetadata {
  preprocessing_version: string;
  embedding_model: string;
  embedding_dimensions: number;
  sentiment_model: string;
  sentiment_license: string;
  ner_model: string;
  topic_model: string;
  trend_weights: Record<string, number>;
  trend_thresholds: Record<string, number>;
  active_run?: {
    id: string;
    dataset_id: string;
    status: string;
    current_step: string;
    progress_pct: number;
    started_at?: string;
  };
  database_backend: string;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public data?: unknown
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function fetchJson<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL.replace(/\/+$/, "")}/${endpoint.replace(/^\/+/, "")}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
  });

  if (!response.ok) {
    let errorData: unknown;
    try {
      errorData = await response.json();
    } catch {
      errorData = null;
    }
    throw new ApiError(
      response.status,
      `API request failed with status ${response.status}`,
      errorData
    );
  }

  return response.json() as Promise<T>;
}

export const api = {
  getHealth: () => fetchJson<HealthCheckResponse>("/health"),

  // Dashboard & Timeline
  getDashboardSummary: (analysisRunId?: string) =>
    fetchJson<DashboardSummary>(
      `/dashboard/summary${analysisRunId ? `?analysis_run_id=${analysisRunId}` : ""}`
    ),

  getTimeline: (analysisRunId?: string, topicId?: string, timeWindow: string = "daily") => {
    const params = new URLSearchParams({ time_window: timeWindow });
    if (analysisRunId) params.append("analysis_run_id", analysisRunId);
    if (topicId) params.append("topic_id", topicId);
    return fetchJson<TimelineResponse>(`/dashboard/timeline?${params.toString()}`);
  },

  // Trends
  getTrends: (analysisRunId?: string, classification?: string, timeWindow: string = "daily") => {
    const params = new URLSearchParams({ time_window: timeWindow });
    if (analysisRunId) params.append("analysis_run_id", analysisRunId);
    if (classification) params.append("classification", classification);
    return fetchJson<{ trends: TrendSnapshot[]; total: number; emerging_count: number; rising_count: number; stable_count: number; declining_count: number }>(
      `/trends?${params.toString()}`
    );
  },

  getTopicTrendHistory: (topicId: string, timeWindow: string = "daily") =>
    fetchJson<TrendSnapshot[]>(`/trends/topic/${topicId}?time_window=${timeWindow}`),

  // Topics
  getTopics: (analysisRunId?: string) =>
    fetchJson<{ topics: TopicItem[]; total: number }>(
      `/topics${analysisRunId ? `?analysis_run_id=${analysisRunId}` : ""}`
    ),

  getTopicDetail: (topicId: string) =>
    fetchJson<TopicDetailResponse>(`/topics/${topicId}`),

  // Datasets & Runs
  getDatasets: () => fetchJson<DatasetItem[]>("/datasets"),

  loadSampleDataset: () =>
    fetchJson<{ message: string; dataset_id: string; row_count: number }>("/datasets/sample", {
      method: "POST",
    }),

  triggerAnalysisRun: (datasetId: string) =>
    fetchJson<{ id: string; status: string; dataset_id: string }>("/analysis/run", {
      method: "POST",
      body: JSON.stringify({ dataset_id: datasetId }),
    }),

  getAnalysisRunStatus: (runId: string) =>
    fetchJson<{ id: string; status: string; progress_pct: number; current_step: string; error_message?: string }>(
      `/analysis/${runId}/status`
    ),

  // Posts Search
  searchPosts: (params: {
    datasetId?: string;
    q?: string;
    sentiment?: string;
    platform?: string;
    topicId?: string;
    limit?: number;
    offset?: number;
  }) => {
    const qp = new URLSearchParams();
    if (params.datasetId) qp.append("dataset_id", params.datasetId);
    if (params.q) qp.append("q", params.q);
    if (params.sentiment) qp.append("sentiment", params.sentiment);
    if (params.platform) qp.append("platform", params.platform);
    if (params.topicId) qp.append("topic_id", params.topicId);
    if (params.limit) qp.append("limit", params.limit.toString());
    if (params.offset) qp.append("offset", params.offset.toString());
    return fetchJson<PostSearchResponse>(`/posts/search?${qp.toString()}`);
  },

  // Pipeline Metadata
  getPipelineMetadata: () => fetchJson<PipelineMetadata>("/pipeline/metadata"),
};
