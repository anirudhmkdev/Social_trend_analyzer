# Social Trend Analyzer — Data Schema

> **Version:** 1.0  
> **Date:** 2026-08-09  
> **Status:** Draft — Awaiting Review  

---

## 1. Entity-Relationship Diagram

```
┌──────────────┐       ┌──────────────┐       ┌──────────────────┐
│   Dataset    │──────<│     Post     │──────<│ SentimentResult  │
│              │  1:N  │              │  1:N  │ (multi-run)      │
│  id          │       │  id          │       │  id              │
│  name        │       │  dataset_id  │       │  post_id         │
│  filename    │       │  ext_id      │       │  analysis_run_id │
│  source_type │       │  original_txt│       │  label           │
│  row_count   │       │  cleaned_txt │       │  confidence      │
│  created_at  │       │  sent_ready  │       │  score_positive  │
│  status      │       │  timestampUTC│       │  score_neutral   │
│  column_map  │       │  platform    │       │  score_negative  │
│  validation  │       │  hashtags    │       └──────────────────┘
│  preproc_ver │       │  likes       │
└──────────────┘       │  comments    │       ┌──────────────────┐
                       │  shares      │──────<│   PostTopic      │
                       │  author_id   │  N:M  │                  │
                       │  mentions    │       │  post_id         │
                       │  urls        │       │  topic_id        │
                       │  is_duplicate│       │  analysis_run_id │
                       │  created_at  │       │  probability     │
                       └──────┬───────┘       │  probability     │
                              │               └────────┬─────────┘
                              │                        │
                              │               ┌────────▼─────────┐
                              │               │     Topic        │
                              │               │                  │
                              │               │  id              │
                              │               │  analysis_run_id │
                              │               │  topic_index     │
                              │               │  display_name    │
                              │               │  keywords_json   │
                              │               │  representative  │
                              │               │  _docs_json      │
                              │               │  post_count      │
                              │               │  is_outlier      │
                              │               └──────────────────┘
                              │
                              │               ┌──────────────────┐
                              ├──────────────<│   PostEntity     │
                              │          N:M  │                  │
                              │               │  post_id         │
                              │               │  entity_id       │
                              │               │  analysis_run_id │
                              │               │  start_char      │
                              │               │  end_char        │
                              │               └────────┬─────────┘
                              │                        │
                              │               ┌────────▼─────────┐
                              │               │     Entity       │
                              │               │                  │
                              │               │  id              │
                              │               │  analysis_run_id │
                              │               │  text            │
                              │               │  normalized_text │
                              │               │  label           │
                              │               │  frequency       │
                              │               └──────────────────┘
                              │
┌──────────────┐              │
│ AnalysisRun  │──────────────┘
│              │  1:N (via analysis_run_id on child tables)
│  id          │
│  dataset_id  │       ┌──────────────────┐
│  status      │──────<│  TrendSnapshot   │
│  progress    │  1:N  │                  │
│  current_step│       │  id              │
│  config_json │       │  analysis_run_id │
│  model_info  │       │  topic_id        │
│  created_at  │       │  time_window     │
│  started_at? │       │  window_start_utc│
│  completed_at│       │  window_end_utc  │
│  error_msg   │       │  trend_score     │
│              │       │  classification  │
│              │       │  explanation     │
│              │       │  volume_current  │
│              │       │  volume_previous │
│              │       │  volume_growth   │
│              │       │  engagement_curr │
│              │       │  engagement_prev │
│              │       │  engagement_grwth│
│              │       │  velocity        │
│              │       │  burst_score     │
│              │       │  recency_score   │
│              │       │  created_at      │
└──────────────┘       └──────────────────┘

                       ┌──────────────────┐
                       │ KeywordSnapshot  │
                       │                  │
                       │  id              │
                       │  analysis_run_id │
                       │  keyword         │
                       │  keyword_type    │
                       │  frequency       │
                       │  tfidf_score     │
                       │  growth_rate     │
                       │  time_window     │
                       │  window_start_utc│
                       │  topic_id (FK?)  │
                       │  created_at      │
                       └──────────────────┘
```

---

## 2. Table Definitions

### 2.1 `datasets`

Represents an uploaded or loaded dataset. Preprocessing is canonical at the dataset level for v1.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, auto | Unique identifier |
| `name` | VARCHAR(255) | NOT NULL | User-facing dataset name |
| `filename` | VARCHAR(500) | NOT NULL | Original filename |
| `source_type` | VARCHAR(50) | NOT NULL | `csv`, `json`, `sample` |
| `file_size_bytes` | BIGINT | | File size in bytes |
| `row_count` | INTEGER | | Number of rows after import |
| `valid_row_count` | INTEGER | | Rows passing validation |
| `column_mapping` | JSONB / PortableJSON | | Map of original → normalized column names |
| `validation_results` | JSONB / PortableJSON | | Validation summary (missing, invalid, duplicates) |
| `preprocessing_version` | VARCHAR(20) | NOT NULL, default '1.0.0' | Canonical preprocessing pipeline version |
| `status` | VARCHAR(50) | NOT NULL | `uploaded`, `mapped`, `validated`, `imported`, `error` |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, default NOW (UTC) | Creation timestamp in UTC |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL (UTC) | Last update timestamp in UTC |

### 2.2 `posts`

Normalized social-media posts. All timestamps are strictly converted and stored in **UTC**.

> **Preprocessing Immutability & Text Representations:**
> - `original_text`: Raw, unaltered text as uploaded. Never overwritten or discarded.
> - `cleaned_text`: Lowercased, stripped of URLs, mentions normalized/removed, hashtag `#` removed, emojis converted/stripped, whitespace collapsed. Used for BERTopic embeddings, TF-IDF, c-TF-IDF keyword extraction, and search indexing.
> - `sentiment_ready_text`: Case-preserved, mentions normalized to `@user`, URLs to `http`. Matches CardiffNLP model pretraining.
> - *NER Text Representation:* spaCy NER operates on a case-preserving text representation derived deterministically at pipeline runtime from `original_text` (HTML unescaped, URLs stripped, casing retained). To prevent redundant storage across thousands of rows, `ner_ready_text` is NOT stored as a separate column.
> - *Canonical Dataset Preprocessing:* Preprocessing is dataset-scoped, canonical and immutable for `preprocessing_version="1.0.0"`. It executes once for a dataset when the preprocessing stage is run (Phase 3), before NLP analysis. Subsequent `AnalysisRuns` reuse the canonical preprocessed representations rather than overwriting them. For v1, preprocessing configuration is fixed/versioned rather than configurable independently for each AnalysisRun, preserving reproducibility without coupling Phase 2 to Phase 3.

> **Missing Engagement vs. Genuine Zero Engagement:**
> Numeric zero engagement (`likes = 0`, `comments = 0`, `shares = 0`) is a valid and legitimate measurement indicating that a post received no interactions. It is **NOT** treated as missing engagement. The trend engine redistributes engagement signal weight ($w_{\text{eng}} \to 0$) only when engagement metrics are unavailable / unmapped in the source dataset (determined via `dataset.column_mapping`), never simply because their values are zero. When engagement metrics are mapped and present with zero values, the engagement signal remains active with $e_g = 0 \implies S(0) = 0.50$. Do not fabricate missing engagement values.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, auto | Internal unique ID |
| `dataset_id` | UUID | FK → datasets.id, NOT NULL | Parent dataset |
| `external_id` | VARCHAR(255) | | Original post ID from source |
| `original_text` | TEXT | NOT NULL | Raw unmodified text |
| `cleaned_text` | TEXT | | Preprocessed lowercased text |
| `sentiment_ready_text` | TEXT | | Text variant aligned for sentiment model |
| `timestamp` | TIMESTAMP WITH TIME ZONE | NOT NULL | Post publication time (normalized to UTC) |
| `platform` | VARCHAR(50) | | Source platform (twitter, reddit, etc.) |
| `hashtags` | JSONB / PortableJSON | | Extracted hashtags list |
| `likes` | INTEGER | nullable | Like/upvote count (NULL if unmapped in dataset; 0 if genuinely zero) |
| `comments` | INTEGER | nullable | Comment/reply count (NULL if unmapped in dataset; 0 if genuinely zero) |
| `shares` | INTEGER | nullable | Share/retweet count (NULL if unmapped in dataset; 0 if genuinely zero) |
| `author_id` | VARCHAR(255) | | Anonymized author identifier |
| `mentions` | JSONB / PortableJSON | | Extracted @mentions list |
| `urls` | JSONB / PortableJSON | | Extracted URLs list |
| `is_duplicate` | BOOLEAN | default FALSE | Duplicate flag |
| `preprocessing_meta` | JSONB / PortableJSON | | Stats about what was cleaned |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, default NOW (UTC) | Record creation time in UTC |

**Indexes:**
- `idx_posts_dataset_id` on `dataset_id`
- `idx_posts_timestamp` on `timestamp`
- `idx_posts_platform` on `platform`
- `idx_posts_text_search` — full-text search index on `cleaned_text` (PostgreSQL `GIN`)

### 2.3 `analysis_runs`

Tracks each NLP pipeline execution lifecycle. An analysis run transitions from `pending` (enqueued) → `running` (processing) → `completed` or `failed`.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, auto | Run identifier |
| `dataset_id` | UUID | FK → datasets.id, NOT NULL | Target dataset |
| `status` | VARCHAR(50) | NOT NULL | `pending`, `running`, `completed`, `failed` |
| `progress_pct` | INTEGER | default 0 | 0–100 progress percentage |
| `current_step` | VARCHAR(100) | | Current pipeline step name |
| `config` | JSONB / PortableJSON | NOT NULL | Full pipeline configuration used |
| `model_info` | JSONB / PortableJSON | | Models, versions, and licenses used |
| `stats` | JSONB / PortableJSON | | Processing statistics (counts, timings) |
| `error_message` | TEXT | | Error details if failed |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, default NOW (UTC) | When the run was enqueued |
| `started_at` | TIMESTAMP WITH TIME ZONE | NULLABLE | NULL while pending; set when processing actually begins |
| `completed_at` | TIMESTAMP WITH TIME ZONE | NULLABLE | NULL while pending/running; set upon completion or failure |

### 2.4 `topics`

Discovered topics from BERTopic.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, auto | |
| `analysis_run_id` | UUID | FK → analysis_runs.id, NOT NULL | |
| `topic_index` | INTEGER | NOT NULL | BERTopic topic ID (−1 = outlier) |
| `display_name` | VARCHAR(255) | NOT NULL | Generated topic name |
| `keywords` | JSONB / PortableJSON | NOT NULL | Top keywords with scores: `[{"word": str, "score": float}]` |
| `representative_docs` | JSONB / PortableJSON | | Top-5 representative post texts |
| `post_count` | INTEGER | NOT NULL | Posts in this topic |
| `is_outlier` | BOOLEAN | default FALSE | True if topic_index = −1 |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, default NOW (UTC) | |

**Indexes:**
- `idx_topics_analysis_run` on `analysis_run_id`
- `idx_topics_index` on `(analysis_run_id, topic_index)` UNIQUE

### 2.5 `post_topics`

Junction table: posts ↔ topics (many-to-many).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, auto | |
| `post_id` | UUID | FK → posts.id, NOT NULL | |
| `topic_id` | UUID | FK → topics.id, NOT NULL | |
| `analysis_run_id` | UUID | FK → analysis_runs.id, NOT NULL | |
| `probability` | FLOAT | | Assignment probability (if available) |

**Indexes:**
- `idx_post_topics_post` on `post_id`
- `idx_post_topics_topic` on `topic_id`
- UNIQUE on `(post_id, topic_id, analysis_run_id)`

### 2.6 `sentiment_results`

Per-post sentiment predictions.

> **Multi-Run Relationship Note:** Multiple `AnalysisRuns` may analyze the same dataset (e.g., testing different pipeline parameters or model updates). Therefore, a single `Post` has a **1:N relationship** with `SentimentResult` across different runs. Within a single analysis run, each post has exactly one prediction, enforced by the compound unique constraint `UNIQUE (post_id, analysis_run_id)`.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, auto | |
| `post_id` | UUID | FK → posts.id, NOT NULL | FK to Post |
| `analysis_run_id` | UUID | FK → analysis_runs.id, NOT NULL | FK to AnalysisRun |
| `label` | VARCHAR(20) | NOT NULL | `positive`, `neutral`, `negative` |
| `confidence` | FLOAT | NOT NULL | Max class probability |
| `score_positive` | FLOAT | NOT NULL | P(positive) |
| `score_neutral` | FLOAT | NOT NULL | P(neutral) |
| `score_negative` | FLOAT | NOT NULL | P(negative) |

**Indexes:**
- `idx_sentiment_post` on `post_id`
- `idx_sentiment_run` on `analysis_run_id`
- `idx_sentiment_label` on `(analysis_run_id, label)`
- UNIQUE on `(post_id, analysis_run_id)`

### 2.7 `entities`

Unique named entities (deduplicated).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, auto | |
| `analysis_run_id` | UUID | FK → analysis_runs.id, NOT NULL | |
| `text` | VARCHAR(255) | NOT NULL | Original entity text |
| `normalized_text` | VARCHAR(255) | NOT NULL | Lowercased/cleaned text |
| `label` | VARCHAR(50) | NOT NULL | Entity type (PERSON, ORG, GPE, etc.) |
| `frequency` | INTEGER | NOT NULL, default 1 | Total occurrences |

**Indexes:**
- `idx_entities_run` on `analysis_run_id`
- UNIQUE on `(analysis_run_id, normalized_text, label)`

### 2.8 `post_entities`

Junction table: posts ↔ entities.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, auto | |
| `post_id` | UUID | FK → posts.id, NOT NULL | |
| `entity_id` | UUID | FK → entities.id, NOT NULL | |
| `analysis_run_id` | UUID | FK → analysis_runs.id, NOT NULL | |
| `start_char` | INTEGER | | Character offset start |
| `end_char` | INTEGER | | Character offset end |

**Indexes:**
- `idx_post_entities_post` on `post_id`
- `idx_post_entities_entity` on `entity_id`

### 2.9 `trend_snapshots`

Pre-computed trend scores for each topic in each time window. All window boundaries are strictly aligned to UTC.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, auto | |
| `analysis_run_id` | UUID | FK → analysis_runs.id, NOT NULL | |
| `topic_id` | UUID | FK → topics.id, NOT NULL | |
| `time_window` | VARCHAR(20) | NOT NULL | `hourly`, `daily`, `weekly` |
| `window_start` | TIMESTAMP WITH TIME ZONE | NOT NULL (UTC) | Start of the UTC analysis window |
| `window_end` | TIMESTAMP WITH TIME ZONE | NOT NULL (UTC) | End of the UTC analysis window |
| `trend_score` | FLOAT | NOT NULL | Modulated composite TrendScore (0–1, 0.50=neutral) |
| `classification` | VARCHAR(20) | NOT NULL | `emerging`, `rising`, `stable`, `declining` |
| `explanation` | TEXT | NOT NULL | Human-readable explanation with std dev burst metrics |
| `volume_current` | INTEGER | NOT NULL | Posts in current window |
| `volume_previous` | INTEGER | NOT NULL | Posts in previous window |
| `volume_growth_pct` | FLOAT | | Percentage change |
| `engagement_current` | FLOAT | | Avg engagement current |
| `engagement_previous` | FLOAT | | Avg engagement previous |
| `engagement_growth_pct` | FLOAT | | Percentage change |
| `velocity` | FLOAT | | Rate of growth acceleration |
| `burst_score` | FLOAT | | Statistical z-score (std devs from baseline) |
| `recency_score` | FLOAT | | Exponential decay modulation factor (0, 1] |
| `sentiment_positive_pct` | FLOAT | | % positive in window |
| `sentiment_neutral_pct` | FLOAT | | % neutral in window |
| `sentiment_negative_pct` | FLOAT | | % negative in window |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, default NOW (UTC) | Creation time in UTC |

**Indexes:**
- `idx_trend_run` on `analysis_run_id`
- `idx_trend_topic` on `topic_id`
- `idx_trend_score` on `(analysis_run_id, trend_score DESC)`
- UNIQUE on `(analysis_run_id, topic_id, time_window, window_start)`

### 2.10 `keyword_snapshots`

Keyword and hashtag trending data.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, auto | |
| `analysis_run_id` | UUID | FK → analysis_runs.id, NOT NULL | |
| `keyword` | VARCHAR(255) | NOT NULL | The keyword or hashtag |
| `keyword_type` | VARCHAR(20) | NOT NULL | `keyword`, `hashtag`, `ngram` |
| `frequency` | INTEGER | NOT NULL | Occurrence count |
| `tfidf_score` | FLOAT | | TF-IDF or c-TF-IDF score |
| `growth_rate` | FLOAT | | Growth vs previous window |
| `time_window` | VARCHAR(20) | | Time window used |
| `window_start` | TIMESTAMP | | Window start if time-scoped |
| `topic_id` | UUID | FK → topics.id, nullable | Associated topic (if topic-level) |
| `created_at` | TIMESTAMP | NOT NULL, default NOW | |

**Indexes:**
- `idx_keyword_run` on `analysis_run_id`
- `idx_keyword_type` on `(analysis_run_id, keyword_type)`
- `idx_keyword_freq` on `(analysis_run_id, keyword_type, frequency DESC)`

---

## 3. Normalized Input Data Format

The ingestion layer normalizes all uploaded data into this internal format before inserting into `posts`:

```json
{
  "external_id": "tweet_12345",
  "text": "Original post text #hashtag @user",
  "timestamp": "2026-07-15T14:30:00Z",
  "platform": "twitter",
  "hashtags": ["hashtag"],
  "likes": 42,
  "comments": 5,
  "shares": 12,
  "author_id": "anon_user_001",
  "source_columns": {
    "text": "tweet_text",
    "timestamp": "created_at",
    "likes": "favorite_count"
  }
}
```

### 3.1 Required Fields

| Field | Required | Fallback |
|-------|----------|----------|
| `text` | **Yes** | Row is rejected if missing |
| `timestamp` | **Yes** | Row is rejected if missing/unparseable |
| `platform` | No | Default: `"unknown"` |
| `hashtags` | No | Extracted from text during preprocessing |
| `likes` | No | Default: `0` |
| `comments` | No | Default: `0` |
| `shares` | No | Default: `0` |
| `author_id` | No | Default: `null` |

### 3.2 Timestamp Parsing & UTC Normalization

All timestamps imported into the system MUST be converted and stored in **UTC**:
- ISO 8601: `2026-07-15T14:30:00Z` or `2026-07-15T10:30:00-04:00` → normalized to `2026-07-15T14:30:00Z`
- Twitter format: `Mon Jul 15 14:30:00 +0000 2026` → normalized to `2026-07-15T14:30:00Z`
- Unix timestamp: `1752587400` → converted to UTC datetime
- Date-only: `2026-07-15` → `2026-07-15T00:00:00Z`

**UTC Normalization Rule:**
All parsed datetimes are converted to timezone-aware UTC (`datetime.timezone.utc`). If an input timestamp is timezone-naive, it is assumed to be UTC. All temporal queries, window aggregations (hourly/daily/weekly), and database records operate strictly in UTC without local timezone bias.

---

## 4. JSONB Field Schemas

### 4.1 `datasets.column_mapping`

```json
{
  "text": "tweet_body",
  "timestamp": "created_at",
  "platform": null,
  "hashtags": "tags",
  "likes": "favorite_count",
  "comments": "reply_count",
  "shares": "retweet_count",
  "author_id": "user_screen_name"
}
```

### 4.2 `datasets.validation_results`

```json
{
  "total_rows": 1000,
  "valid_rows": 948,
  "invalid_rows": 52,
  "issues": {
    "missing_text": 10,
    "missing_timestamp": 8,
    "invalid_timestamp": 15,
    "duplicate_posts": 19
  },
  "platform_distribution": {
    "twitter": 450,
    "reddit": 320,
    "instagram": 230
  },
  "date_range": {
    "earliest": "2026-07-01T00:00:00Z",
    "latest": "2026-07-31T23:59:59Z"
  },
  "missing_field_counts": {
    "hashtags": 120,
    "author_id": 50,
    "likes": 30
  }
}
```

### 4.3 `analysis_runs.config`

```json
{
  "pipeline_version": "1.0.0",
  "dataset_preprocessing_version": "1.0.0",
  "random_seed": 42,
  "embedding_model": "all-MiniLM-L6-v2",
  "sentiment_model": "cardiffnlp/twitter-roberta-base-sentiment-latest",
  "ner_model": "en_core_web_sm",
  "umap": {
    "n_neighbors": 15,
    "n_components": 5,
    "min_dist": 0.0,
    "metric": "cosine",
    "random_state": 42
  },
  "hdbscan": {
    "min_cluster_size": 10,
    "min_samples": 5,
    "metric": "euclidean"
  },
  "bertopic": {
    "nr_topics": null
  },
  "trend_scoring": {
    "weight_volume": 0.35,
    "weight_engagement": 0.25,
    "weight_velocity": 0.20,
    "weight_burstiness": 0.20,
    "time_window": "daily",
    "min_baseline": 1.0,
    "decay_rate": 0.05,
    "threshold_emerging": 0.70,
    "threshold_rising": 0.60,
    "threshold_stable": 0.40
  },
  "preprocessing": {
    "emoji_handling": "convert_to_text",
    "min_text_length": 5
  }
}
```

### 4.4 `topics.keywords`

```json
[
  {"word": "climate", "score": 0.0842},
  {"word": "emissions", "score": 0.0715},
  {"word": "carbon", "score": 0.0653},
  {"word": "energy", "score": 0.0591},
  {"word": "renewable", "score": 0.0524}
]
```

### 4.5 `analysis_runs.model_info`

```json
{
  "embedding": {
    "name": "all-MiniLM-L6-v2",
    "dimensions": 384,
    "source": "sentence-transformers"
  },
  "sentiment": {
    "name": "cardiffnlp/twitter-roberta-base-sentiment-latest",
    "license": "CC-BY-4.0",
    "training": "~124M tweets",
    "labels": ["negative", "neutral", "positive"],
    "source": "huggingface-transformers"
  },
  "ner": {
    "name": "en_core_web_sm",
    "version": "3.8.0",
    "source": "spacy",
    "input_representation": "case-preserved (runtime)"
  },
  "topic_modeling": {
    "name": "BERTopic",
    "version": "0.17.4",
    "nr_topics": null
  }
}
```

---

## 5. Migration Strategy

### 5.1 Approach

Use **Alembic** for database migrations.

### 5.2 Dual Database Support & Explicit Dialect-Aware JSON

In SQLAlchemy, generic `Column(JSON)` compiles to plain `JSON` or `TEXT` and does **not** provide PostgreSQL `JSONB` binary storage or `GIN` indexing semantics.

To ensure native `JSONB` on PostgreSQL while maintaining full compatibility with SQLite for zero-setup local runs, models must use SQLAlchemy's `.with_variant()` pattern:

```python
from sqlalchemy import Column, JSON
from sqlalchemy.dialects.postgresql import JSONB

# Portable JSON type: uses native PostgreSQL JSONB (binary JSON + GIN indexing support)
# on PostgreSQL, and standard JSON/TEXT on SQLite.
PortableJSON = JSON().with_variant(JSONB(), "postgresql")

# Example usage in models:
column_mapping = Column(PortableJSON, nullable=True)
validation_results = Column(PortableJSON, nullable=True)
hashtags = Column(PortableJSON, nullable=True)
config = Column(PortableJSON, nullable=False)
```

### 5.3 Phase Plan

| Phase | Migration | Tables Created |
|-------|-----------|---------------|
| Phase 1 | `001_initial` | `datasets`, `posts` |
| Phase 2 | (uses Phase 1 tables) | — |
| Phase 3 | `002_preprocessing` | Add `cleaned_text`, `sentiment_ready_text`, preprocessing columns to `posts` |
| Phase 4 | `003_sentiment` | `analysis_runs`, `sentiment_results` |
| Phase 5 | `004_topics` | `topics`, `post_topics` |
| Phase 6 | `005_entities_keywords` | `entities`, `post_entities`, `keyword_snapshots` |
| Phase 7 | `006_trends` | `trend_snapshots` |
