# Social Trend Analyzer — Product Requirements Document

> **Version:** 1.0  
> **Date:** 2026-08-09  
> **Status:** Draft — Awaiting Review  
> **Author:** NLP Project Team  

---

## 1. Executive Summary

**Social Trend Analyzer** is an NLP-powered web application that ingests social-media post datasets and automatically discovers emerging topics, trending keywords/hashtags, sentiment patterns, named entities, engagement dynamics, and temporal trends. It surfaces these insights through a professional, interactive analytics dashboard.

This is an **academic NLP project** designed to demonstrate practical competence in modern NLP techniques (transformer-based sentiment analysis, BERTopic topic modeling, NER, trend detection algorithms) while remaining fully runnable on a single development machine without requiring paid APIs or live social-media credentials.

---

## 2. Problem Statement

Social media generates enormous volumes of unstructured text. Manually identifying what topics are gaining traction, how public sentiment is shifting, and which entities are associated with emerging trends is infeasible at scale. Existing commercial solutions (Brandwatch, Sprout Social, Meltwater) require enterprise budgets and live API access.

This project demonstrates that a local, self-contained NLP pipeline can:

1. Automatically discover latent topics from social-media text.
2. Detect which topics are genuinely *trending* (not merely frequent).
3. Explain *why* something is trending with computed statistics.
4. Classify post-level sentiment using pretrained transformers.
5. Extract named entities and associate them with trends.
6. Present all results through a data-dense analytics dashboard.

---

## 3. Target Users

| Persona | Description |
|---------|-------------|
| **College Evaluator** | Faculty/examiner assessing the NLP pipeline, architecture, and academic rigor. |
| **Student Demonstrator** | The project owner running the demo with bundled sample data. |
| **Curious Analyst** | Anyone uploading their own CSV/JSON dataset to explore trends. |

---

## 4. User Stories

### 4.1 Dataset Management

| ID | Story | Priority |
|----|-------|----------|
| US-01 | As a user, I can upload a CSV file containing social-media posts. | P0 |
| US-02 | As a user, I can load the bundled sample dataset with one click. | P0 |
| US-03 | As a user, I can preview uploaded data (columns, rows, types). | P0 |
| US-04 | As a user, I can map CSV columns to the expected schema when auto-detection fails. | P0 |
| US-05 | As a user, I see validation results (missing values, bad timestamps, duplicates, row count). | P0 |
| US-06 | As a user, I can upload a JSON file containing social-media posts. | P1 |

### 4.2 NLP Analysis

| ID | Story | Priority |
|----|-------|----------|
| US-10 | As a user, I can trigger NLP analysis on an imported dataset. | P0 |
| US-11 | As a user, I can see the processing status and progress of the analysis. | P0 |
| US-12 | As a user, sentiment is classified as Positive/Neutral/Negative with confidence scores. | P0 |
| US-13 | As a user, topics are automatically discovered without me specifying the number of topics. | P0 |
| US-14 | As a user, named entities (people, orgs, locations, products, events) are extracted. | P0 |
| US-15 | As a user, hashtags and keywords are extracted and ranked. | P0 |

### 4.3 Trend Detection

| ID | Story | Priority |
|----|-------|----------|
| US-20 | As a user, I can see which topics are trending (not just which are most frequent). | P0 |
| US-21 | As a user, each trend includes a human-readable explanation of *why* it is trending. | P0 |
| US-22 | As a user, trends are classified as Emerging / Rising / Stable / Declining. | P0 |
| US-23 | As a user, I can configure the time window (hourly/daily/weekly) for trend analysis. | P1 |

### 4.4 Dashboard & Exploration

| ID | Story | Priority |
|----|-------|----------|
| US-30 | As a user, the main dashboard shows summary cards, trending topics, sentiment, hashtags, keywords, entities, and activity charts. | P0 |
| US-31 | As a user, I can click a topic to see a detailed trend analysis page. | P0 |
| US-32 | As a user, I can search/filter results by keyword, topic, platform, and date range. | P1 |
| US-33 | As a user, I can see representative posts for each topic. | P0 |
| US-34 | As a user, I can see platform distribution of posts. | P1 |

### 4.5 Academic / Pipeline Transparency

| ID | Story | Priority |
|----|-------|----------|
| US-40 | As a user, I can view an "Analysis" page explaining the NLP pipeline, models used, and dataset/processing statistics. | P0 |
| US-41 | As a user, I can see evaluation metrics (accuracy, F1, etc.) if ground-truth labels exist. | P1 |

---

## 5. Functional Requirements

### 5.1 Data Ingestion

- **FR-01:** Accept CSV uploads (required) and JSON uploads (stretch).
- **FR-02:** Auto-detect column mappings for known field names (`text`, `timestamp`, `platform`, `hashtags`, `likes`, `comments`, `shares`, `author`).
- **FR-03:** Provide manual column-mapping UI when auto-detection is ambiguous.
- **FR-04:** Validate: missing required fields (`text`, `timestamp`), invalid timestamp formats, duplicate rows. All parsed timestamps normalized to timezone-aware UTC.
- **FR-05:** Report validation summary before committing the import.
- **FR-06:** Store both raw/original and normalized data. Preprocessing is canonical at the dataset level and versioned.
- **FR-07:** Bundle a clearly-labeled synthetic demo dataset (~500–1000 posts) covering multiple topics, sentiment distributions, UTC time ranges, platforms, and engagement levels.

### 5.2 NLP Pipeline

- **FR-10:** Text preprocessing: URL extraction/replacement, mention normalization, hashtag extraction, emoji handling, whitespace normalization. Store `original_text`, `cleaned_text` (lowercased), and `sentiment_ready_text` (`@user`, `http`). NER operates on case-preserved text derived deterministically at runtime.
- **FR-11:** Sentiment analysis via `cardiffnlp/twitter-roberta-base-sentiment-latest` (License: CC-BY-4.0). Store label + confidence scores. Support batch inference using `sentiment_ready_text`.
- **FR-12:** Topic modeling via Sentence Transformers (`all-MiniLM-L6-v2`) → UMAP (`random_state=42`) → HDBSCAN → BERTopic/c-TF-IDF initialized with `nr_topics=None` to preserve natural clusters. Allow outlier/unclassified posts.
- **FR-13:** Each topic: `topic_id`, generated name, keywords, representative posts, post count, sentiment distribution, engagement stats, timestamps.
- **FR-14:** Keyword/hashtag extraction: frequency, growth rate, c-TF-IDF/TF-IDF scoring, n-gram support.
- **FR-15:** NER via spaCy (`en_core_web_sm`): PERSON, ORG, GPE, PRODUCT, EVENT, operating on case-preserved text.
- **FR-16:** All NLP modules must be independently callable and replaceable.

### 5.3 Trend Detection

- **FR-20:** Compute a multi-signal TrendScore per topic using centered logistic-normalized momentum (volume growth, engagement growth, velocity, burstiness z-score) with recency acting strictly as a relevance/modulation factor. Zero growth must be mathematically neutral (classified as Stable).
- **FR-21:** Normalize all momentum components via centered logistic normalization (logistic normalization with 0.5 as the neutral point) so zero change maps to 0.50 (neutral).
- **FR-22:** Handle edge cases: zero historical baseline, tiny sample sizes, division-by-zero, missing engagement redistribution (distinguishing unavailable engagement from genuine zero engagement).
- **FR-23:** Classify: 🔥 Emerging, ↗ Rising, → Stable, ↘ Declining.
- **FR-24:** Generate per-trend explanation strings describing burstiness in standard deviations above/below baseline.
- **FR-25:** Support configurable time windows (hourly, daily, weekly) evaluated in UTC.
- **FR-26:** Compare current UTC window against previous comparable UTC window.

### 5.4 Analytics APIs

- **FR-30:** RESTful API endpoints for: dashboard summary, trending topics, topic detail, sentiment distribution, hashtags, keywords, entities, timeline data, post search/filter.
- **FR-31:** All API responses use Pydantic schemas.
- **FR-32:** Store derived analysis results in the database so the dashboard does not re-trigger the NLP pipeline on every page load.
- **FR-33:** Restrict concurrent analysis runs to 1 active job at a time in the single-machine demo architecture.

### 5.5 Dashboard

- **FR-40:** Summary cards: posts analyzed, active topics, emerging trends, overall sentiment breakdown.
- **FR-41:** Trending topics table: topic name, trend score, change %, sentiment, post volume, direction indicator.
- **FR-42:** Activity timeline chart (line/area).
- **FR-43:** Sentiment distribution chart.
- **FR-44:** Trending hashtags list/chart.
- **FR-45:** Trending keywords list/chart.
- **FR-46:** Trending entities list.
- **FR-47:** Platform distribution chart.
- **FR-48:** Recent/representative posts panel.

### 5.6 Trend Detail Page

- **FR-50:** Topic name, trend score, status badge, trend explanation.
- **FR-51:** Keywords and related hashtags.
- **FR-52:** Representative posts with sentiment labels.
- **FR-53:** Volume timeline chart.
- **FR-54:** Sentiment timeline chart.
- **FR-55:** Sentiment distribution (pie/donut).
- **FR-56:** Engagement statistics.
- **FR-57:** Related entities.
- **FR-58:** Related topics (if feasible).

### 5.7 Pipeline / Analysis Page

- **FR-60:** Visual pipeline diagram (Text → Preprocessing → Embeddings → Topic Modeling → Sentiment/NER/Keywords → Temporal Aggregation → Trend Detection → Dashboard).
- **FR-61:** Models used with versions and licenses (including CardiffNLP CC-BY-4.0).
- **FR-62:** Dataset statistics (row count, date range, platforms, missing data %).
- **FR-63:** Preprocessing statistics (URLs removed, mentions normalized, etc.).
- **FR-64:** Topic statistics (topic count, avg size, outlier count).
- **FR-65:** Evaluation metrics if ground-truth labels exist (accuracy, precision, recall, F1, confusion matrix).

---

## 6. Non-Functional Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-01 | The application runs entirely locally without paid APIs. | Mandatory |
| NFR-02 | NLP pipeline processes 1000 posts in < 5 minutes on a modern laptop (CPU). | Goal |
| NFR-03 | Dashboard loads cached results in < 2 seconds. | Goal |
| NFR-04 | Backend test coverage ≥ 70% for NLP and trend logic. | Goal |
| NFR-05 | All dependencies pinned in committed lockfiles (`requirements.lock`, `package-lock.json`). | Mandatory |
| NFR-06 | Deterministic random seeds for reproducible analysis. | Mandatory |
| NFR-07 | No secrets committed; `.env.example` provided. | Mandatory |
| NFR-08 | Responsive desktop layout (1024px+). | Mandatory |
| NFR-09 | Proper loading, empty, and error states in the UI. | Mandatory |

---

## 7. Out of Scope (v1)

- Live social-media API connectors (Twitter/X, Reddit, Instagram).
- User authentication / multi-tenancy.
- Real-time streaming analysis.
- GPU-only deployment requirements.
- Mobile-optimized layout.
- Multilingual support (English only for v1).
- Custom model training/fine-tuning in the UI.

---

## 8. Success Criteria

1. A user can load the sample dataset and see a fully populated dashboard within 5 minutes of starting the application.
2. The trend detection algorithm identifies at least 2 distinct trending topics from the sample data and explains why each is trending.
3. Sentiment labels are assigned to all posts with confidence scores.
4. Topics are automatically discovered without hardcoded topic counts.
5. The pipeline page accurately reflects the actual models and parameters used.
6. An evaluator can understand the NLP methodology by reading the code, documentation, and pipeline page.

---

## 9. Bundled Sample Dataset Specification

The synthetic demo dataset must contain:

| Requirement | Detail |
|-------------|--------|
| Size | 500–1000 posts |
| Topics | ≥ 5 distinct themes (e.g., AI/Tech, Climate, Sports, Entertainment, Politics) |
| Sentiment | Mix of positive, neutral, negative per topic |
| Platforms | ≥ 3 simulated platforms (e.g., twitter, reddit, instagram) |
| Time Span | ≥ 14 days with varying posting volumes |
| Trends | At least 1 rising topic, 1 declining topic, 1 stable topic |
| Engagement | Varying likes/comments/shares |
| Entities | Real-sounding but anonymized person/org/location names |
| Hashtags | 15–30 distinct hashtags distributed across topics |
| Label | Clearly marked as `source: "synthetic_demo"` |

---

## 10. Glossary

| Term | Definition |
|------|------------|
| **BERTopic** | A topic modeling technique using transformer embeddings, UMAP, HDBSCAN, and c-TF-IDF. |
| **c-TF-IDF** | Class-based TF-IDF — a technique that treats all documents in a cluster as a single document to extract representative terms. |
| **Trend Score** | A composite metric quantifying how much a topic's attention is changing relative to its baseline. |
| **Burstiness** | A sudden, abnormal spike in activity compared to historical norms. |
| **NER** | Named Entity Recognition — extracting structured entities (people, organizations, etc.) from text. |
| **UMAP** | Uniform Manifold Approximation and Projection — a dimensionality reduction technique. |
| **HDBSCAN** | Hierarchical Density-Based Spatial Clustering of Applications with Noise. |
