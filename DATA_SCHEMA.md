# Implemented database schema

Generated from the current SQLAlchemy metadata. UUID keys; UTC timestamps; JSON uses portable JSON/JSONB. SQLite foreign keys are enabled; dataset deletion cascades runs and posts, and their derived results.

Migrations: `001_initial`, `002_nlp_and_trends`, `003_staged_uploads`, `004_topic_provenance`, `005_legacy_provenance`. New nullable staging/provenance columns preserve existing databases. Never modify existing historical migrations to disguise schema drift. Redundant automatic indexes were removed from ORM declarations so metadata agrees with the existing named migration indexes.

## datasets

| Column | Type | Nullable | Key / reference |
|---|---|---|---|
| `id` | CHAR(32) | False | PK |
| `name` | VARCHAR(255) | False |  |
| `filename` | VARCHAR(500) | False |  |
| `staged_filename` | VARCHAR(50) | True |  |
| `upload_metadata` | JSON | True |  |
| `source_type` | VARCHAR(50) | False |  |
| `file_size_bytes` | BIGINT | True |  |
| `row_count` | INTEGER | True |  |
| `valid_row_count` | INTEGER | True |  |
| `column_mapping` | JSON | True |  |
| `validation_results` | JSON | True |  |
| `preprocessing_version` | VARCHAR(20) | False |  |
| `status` | VARCHAR(50) | False |  |
| `created_at` | DATETIME | False |  |
| `updated_at` | DATETIME | False |  |

Indexes:

## analysis_runs

| Column | Type | Nullable | Key / reference |
|---|---|---|---|
| `id` | CHAR(32) | False | PK |
| `dataset_id` | CHAR(32) | False | datasets.id (CASCADE) |
| `status` | VARCHAR(50) | False |  |
| `progress_pct` | INTEGER | False |  |
| `current_step` | VARCHAR(100) | True |  |
| `config` | JSON | False |  |
| `model_info` | JSON | True |  |
| `stats` | JSON | True |  |
| `error_message` | TEXT | True |  |
| `created_at` | DATETIME | False |  |
| `started_at` | DATETIME | True |  |
| `completed_at` | DATETIME | True |  |

Indexes: `idx_analysis_runs_dataset_id`, `idx_analysis_runs_status`

## posts

| Column | Type | Nullable | Key / reference |
|---|---|---|---|
| `id` | CHAR(32) | False | PK |
| `dataset_id` | CHAR(32) | False | datasets.id (CASCADE) |
| `external_id` | VARCHAR(255) | True |  |
| `original_text` | TEXT | False |  |
| `cleaned_text` | TEXT | True |  |
| `sentiment_ready_text` | TEXT | True |  |
| `timestamp` | DATETIME | False |  |
| `platform` | VARCHAR(50) | True |  |
| `hashtags` | JSON | True |  |
| `likes` | INTEGER | True |  |
| `comments` | INTEGER | True |  |
| `shares` | INTEGER | True |  |
| `author_id` | VARCHAR(255) | True |  |
| `mentions` | JSON | True |  |
| `urls` | JSON | True |  |
| `is_duplicate` | BOOLEAN | False |  |
| `preprocessing_meta` | JSON | True |  |
| `created_at` | DATETIME | False |  |

Indexes: `idx_posts_dataset_id`, `idx_posts_platform`, `idx_posts_timestamp`

## entities

| Column | Type | Nullable | Key / reference |
|---|---|---|---|
| `id` | CHAR(32) | False | PK |
| `analysis_run_id` | CHAR(32) | False | analysis_runs.id (CASCADE) |
| `text` | VARCHAR(255) | False |  |
| `normalized_text` | VARCHAR(255) | False |  |
| `label` | VARCHAR(50) | False |  |
| `frequency` | INTEGER | False |  |

Indexes: `idx_entities_run`

## sentiment_results

| Column | Type | Nullable | Key / reference |
|---|---|---|---|
| `id` | CHAR(32) | False | PK |
| `post_id` | CHAR(32) | False | posts.id (CASCADE) |
| `analysis_run_id` | CHAR(32) | False | analysis_runs.id (CASCADE) |
| `label` | VARCHAR(20) | False |  |
| `confidence` | FLOAT | False |  |
| `score_positive` | FLOAT | False |  |
| `score_neutral` | FLOAT | False |  |
| `score_negative` | FLOAT | False |  |
| `created_at` | DATETIME | False |  |

Indexes: `idx_sentiment_label`, `idx_sentiment_post`, `idx_sentiment_run`

## topics

| Column | Type | Nullable | Key / reference |
|---|---|---|---|
| `id` | CHAR(32) | False | PK |
| `analysis_run_id` | CHAR(32) | False | analysis_runs.id (CASCADE) |
| `topic_index` | INTEGER | False |  |
| `display_name` | VARCHAR(255) | False |  |
| `keywords` | JSON | False |  |
| `representative_docs` | JSON | True |  |
| `model_metadata` | JSON | True |  |
| `post_count` | INTEGER | False |  |
| `is_outlier` | BOOLEAN | False |  |
| `created_at` | DATETIME | False |  |

Indexes: `idx_topics_analysis_run`

## keyword_snapshots

| Column | Type | Nullable | Key / reference |
|---|---|---|---|
| `id` | CHAR(32) | False | PK |
| `analysis_run_id` | CHAR(32) | False | analysis_runs.id (CASCADE) |
| `keyword` | VARCHAR(255) | False |  |
| `keyword_type` | VARCHAR(20) | False |  |
| `frequency` | INTEGER | False |  |
| `tfidf_score` | FLOAT | True |  |
| `growth_rate` | FLOAT | True |  |
| `time_window` | VARCHAR(20) | True |  |
| `window_start` | DATETIME | True |  |
| `topic_id` | CHAR(32) | True | topics.id (SET NULL) |
| `created_at` | DATETIME | False |  |

Indexes: `idx_keyword_freq`, `idx_keyword_run`, `idx_keyword_type`

## post_entities

| Column | Type | Nullable | Key / reference |
|---|---|---|---|
| `id` | CHAR(32) | False | PK |
| `post_id` | CHAR(32) | False | posts.id (CASCADE) |
| `entity_id` | CHAR(32) | False | entities.id (CASCADE) |
| `analysis_run_id` | CHAR(32) | False | analysis_runs.id (CASCADE) |
| `start_char` | INTEGER | True |  |
| `end_char` | INTEGER | True |  |

Indexes: `idx_post_entities_entity`, `idx_post_entities_post`

## post_topics

| Column | Type | Nullable | Key / reference |
|---|---|---|---|
| `id` | CHAR(32) | False | PK |
| `post_id` | CHAR(32) | False | posts.id (CASCADE) |
| `topic_id` | CHAR(32) | False | topics.id (CASCADE) |
| `analysis_run_id` | CHAR(32) | False | analysis_runs.id (CASCADE) |
| `probability` | FLOAT | True |  |

Indexes: `idx_post_topics_post`, `idx_post_topics_topic`

## trend_snapshots

| Column | Type | Nullable | Key / reference |
|---|---|---|---|
| `id` | CHAR(32) | False | PK |
| `analysis_run_id` | CHAR(32) | False | analysis_runs.id (CASCADE) |
| `topic_id` | CHAR(32) | False | topics.id (CASCADE) |
| `time_window` | VARCHAR(20) | False |  |
| `window_start` | DATETIME | False |  |
| `window_end` | DATETIME | False |  |
| `trend_score` | FLOAT | False |  |
| `classification` | VARCHAR(20) | False |  |
| `explanation` | TEXT | False |  |
| `volume_current` | INTEGER | False |  |
| `volume_previous` | INTEGER | False |  |
| `volume_growth_pct` | FLOAT | True |  |
| `engagement_current` | FLOAT | True |  |
| `engagement_previous` | FLOAT | True |  |
| `engagement_growth_pct` | FLOAT | True |  |
| `velocity` | FLOAT | True |  |
| `burst_score` | FLOAT | True |  |
| `recency_score` | FLOAT | True |  |
| `sentiment_positive_pct` | FLOAT | True |  |
| `sentiment_neutral_pct` | FLOAT | True |  |
| `sentiment_negative_pct` | FLOAT | True |  |
| `created_at` | DATETIME | False |  |

Indexes: `idx_trend_run`, `idx_trend_score`, `idx_trend_topic`

## Result identity and lifecycle

Sentiment is unique per post/run. Topic indices are unique within their run. PostTopic links include their run; every search/detail aggregate scopes that link and sentiment join explicitly. Entity and keyword snapshots belong to runs. Stored trend snapshots document daily unfiltered processing; filter/window views recompute from the selected run assignments. UUID staging filenames are internal fields and are not returned to the frontend.

Dataset statuses: uploaded, mapped, validated, imported, preprocessed. Analysis statuses: pending, running, completed, failed. Imported sources are immutable. In-process jobs cannot resume after server restart; old active rows become failed with retry guidance. Failed-run partial evidence is excluded from completed analytics.

Fresh SQLite upgrade, metadata drift check, downgrade-to-base/re-upgrade and cascade regressions are automated. PostgreSQL runtime verification requires a running server and is reported separately in the audit.
