# Social Trend Analyzer — Implementation Roadmap

> **Version:** 1.0  
> **Date:** 2026-08-09  
> **Status:** Draft — Awaiting Review  

---

## Roadmap Summary

| Phase | Name | Est. Effort | Dependencies |
|-------|------|-------------|--------------|
| 0 | Planning & Architecture | ✅ This document | — |
| 1 | Project Foundation | Medium | Phase 0 |
| 2 | Dataset Ingestion | Medium | Phase 1 |
| 3 | NLP Preprocessing | Small–Medium | Phase 2 |
| 4 | Sentiment Analysis | Medium | Phase 3 |
| 5 | Topic Modeling | Medium–Large | Phase 3 |
| 6 | NLP Enrichment (Keywords + NER) | Medium | Phases 4, 5 |
| 7 | Trend Detection Engine | Medium–Large | Phase 6 |
| 8 | Analytics APIs | Medium | Phase 7 |
| 9 | Dashboard | Large | Phase 8 |
| 10 | Trend Investigation (Detail Pages) | Medium | Phase 9 |
| 11 | Evaluation & Testing | Medium | Phase 10 |
| 12 | Documentation & Academic Polish | Medium | Phase 11 |

---

## Phase 0 — Planning & Architecture ✅

**Objective:** Produce all planning documents and establish project structure.

**Deliverables:**
- [x] `PRD.md`
- [x] `ARCHITECTURE.md`
- [x] `NLP_PIPELINE.md`
- [x] `DATA_SCHEMA.md`
- [x] `IMPLEMENTATION_ROADMAP.md` (this file)
- [x] `AGENTS.md`

**Acceptance Criteria:**
- All documents reviewed and approved by the project owner.
- Technology stack confirmed.
- No blocking open questions remain.

---

## Phase 1 — Project Foundation

**Objective:** Scaffold the full project structure, install dependencies, configure linters, set up the database, and verify that both frontend and backend start successfully.

### Tasks

| # | Task | Files |
|---|------|-------|
| 1.1 | Create top-level directory structure | `backend/`, `frontend/`, `docs/`, `.agents/` |
| 1.2 | Initialize Python backend with FastAPI | `backend/app/main.py`, `backend/app/config.py` |
| 1.3 | Create `pyproject.toml` (single source of truth for Python deps) and compile/lock to committed `requirements.lock` (via `pip-compile` / `uv pip compile`) | `backend/pyproject.toml`, `backend/requirements.lock` |
| 1.4 | Set up SQLAlchemy engine with PostgreSQL + SQLite support using `PortableJSON` | `backend/app/database/engine.py`, `backend/app/database/base.py` |
| 1.5 | Configure Alembic for migrations | `backend/app/database/migrations/` |
| 1.6 | Create initial DB models: `Dataset` (with `preprocessing_version`), `Post` (with UTC timestamp, `original_text`, `cleaned_text`, `sentiment_ready_text`) | `backend/app/models/dataset.py`, `backend/app/models/post.py` |
| 1.7 | Run initial Alembic migration | `backend/app/database/migrations/versions/001_initial.py` |
| 1.8 | Set up Ruff + mypy configuration | `backend/pyproject.toml` |
| 1.9 | Create `.env.example` and `config.py` (Pydantic BaseSettings) | `backend/.env.example`, `backend/app/config.py` |
| 1.10 | Initialize Next.js 15 frontend with TypeScript + Tailwind + shadcn/ui using a supported, security-patched Next.js version; commit `package-lock.json` | `frontend/`, `frontend/package-lock.json` |
| 1.11 | Set up ESLint + Prettier | `frontend/` config files |
| 1.12 | Create basic app layout shell (sidebar + header) | `frontend/src/components/layout/` |
| 1.13 | Configure frontend API client | `frontend/src/lib/api.ts` |
| 1.14 | Create `.gitignore` | Root `.gitignore` |
| 1.15 | Set up pytest with conftest | `backend/tests/conftest.py` |
| 1.16 | Write a health-check endpoint + test | `backend/app/api/v1/health.py`, `backend/tests/test_api/test_health.py` |
| 1.17 | Docker Compose for PostgreSQL | `docker-compose.yml` |

### Expected Folder Structure After Phase 1

```
social-trend-analyzer/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── dependencies.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── router.py
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       └── health.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   └── exceptions.py
│   │   ├── database/
│   │   │   ├── __init__.py
│   │   │   ├── engine.py
│   │   │   ├── base.py
│   │   │   └── migrations/
│   │   └── models/
│   │       ├── __init__.py
│   │       ├── dataset.py
│   │       └── post.py
│   ├── tests/
│   │   ├── conftest.py
│   │   └── test_api/
│   │       └── test_health.py
│   ├── pyproject.toml
│   ├── requirements.lock              # Committed Python lockfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   └── page.tsx
│   │   ├── components/
│   │   │   ├── ui/          (shadcn)
│   │   │   └── layout/
│   │   │       ├── Sidebar.tsx
│   │   │       ├── Header.tsx
│   │   │       └── AppShell.tsx
│   │   └── lib/
│   │       └── api.ts
│   ├── package.json
│   ├── package-lock.json              # Committed frontend lockfile
│   ├── tsconfig.json
│   └── tailwind.config.ts
├── docs/
├── .agents/AGENTS.md
├── .gitignore
├── docker-compose.yml
└── README.md
```

### Acceptance Criteria

- [ ] `uvicorn app.main:app` starts on port 8000 without errors.
- [ ] `GET /api/v1/health` returns `200 {"status": "ok"}`.
- [ ] `npm run dev` starts Next.js on port 3000 without errors.
- [ ] Frontend renders the app shell (sidebar + header) with placeholder content.
- [ ] `pytest` passes the health check test.
- [ ] Ruff lint passes with no errors.
- [ ] Alembic migration runs successfully (creates `datasets` and `posts` tables).
- [ ] `.env.example` exists with all required variables documented.
- [ ] Committed `requirements.lock` and `package-lock.json` exist; dependencies install cleanly without manual resolution.

### Verification Commands

```bash
# Backend
cd backend
pip install -r requirements.lock
python -m ruff check app/
python -m mypy app/ --ignore-missing-imports
pytest tests/ -v
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm ci
npm run lint
npm run build
npm run dev

# Database
cd backend
alembic upgrade head
```

### Out of Scope

- NLP models (no downloads yet).
- File upload endpoints (Phase 2).
- Any dashboard content beyond the layout shell.

---

## Phase 2 — Dataset Ingestion

**Objective:** Build the full data import pipeline: file upload, column detection, column mapping UI, validation, normalization, and sample dataset loading. All imported timestamps are strictly normalized to UTC.

### Tasks

| # | Task | Files |
|---|------|-------|
| 2.1 | Create CSV parser with column auto-detection | `backend/app/ingestion/csv_parser.py` |
| 2.2 | Create column mapper (auto-detect + manual override) | `backend/app/ingestion/column_mapper.py` |
| 2.3 | Create data validator (missing text, bad timestamps, duplicates) | `backend/app/ingestion/validator.py` |
| 2.4 | Create data normalizer (to internal Post format with strict UTC timestamp conversion) | `backend/app/ingestion/normalizer.py` |
| 2.5 | Create Pydantic schemas for dataset operations | `backend/app/schemas/dataset.py`, `backend/app/schemas/post.py` |
| 2.6 | Create dataset service | `backend/app/services/dataset_service.py` |
| 2.7 | Create API endpoints: upload, sample, list, detail, preview, map-columns, validate | `backend/app/api/v1/datasets.py` |
| 2.8 | Create synthetic demo dataset (500–1000 posts with UTC timestamps) | `backend/data/sample_dataset.csv` |
| 2.9 | Create sample dataset generation script | `backend/scripts/generate_sample_data.py` |
| 2.10 | Build frontend Dataset page: upload, preview, column mapping, validation results | `frontend/src/app/datasets/page.tsx`, `frontend/src/components/datasets/` |
| 2.11 | Write ingestion unit tests | `backend/tests/test_ingestion/` |
| 2.12 | Write API integration tests | `backend/tests/test_api/test_datasets.py` |

### Acceptance Criteria

- [ ] Upload a CSV file via the API → file is parsed and columns detected.
- [ ] Column auto-detection correctly maps common field names (text, timestamp, likes, etc.).
- [ ] Manual column mapping works when auto-detection fails.
- [ ] All parsed timestamps are normalized to timezone-aware UTC (`posts.timestamp`).
- [ ] Validation reports: missing text count, invalid timestamps, duplicate rows, total/valid row counts.
- [ ] Invalid data is flagged but NOT silently discarded.
- [ ] `POST /api/v1/datasets/sample` loads the bundled sample dataset.
- [ ] Frontend shows file upload, data preview (first 10 rows), column mapper, and validation results.
- [ ] Sample dataset contains 500+ posts across 5+ topics, 3+ platforms, 14+ days, with engagement data.
- [ ] All ingestion tests pass.

### Verification Commands

```bash
cd backend
pytest tests/test_ingestion/ -v
pytest tests/test_api/test_datasets.py -v
# Manual: upload sample_dataset.csv via frontend
```

### Out of Scope

- JSON file support (stretch goal).
- NLP preprocessing (Phase 3).
- Analysis triggering (Phase 4+).

---

## Phase 3 — NLP Preprocessing

**Objective:** Implement canonical dataset-level text cleaning and normalization for all posts in a dataset, producing `cleaned_text` and `sentiment_ready_text`, and provide deterministic runtime case-preserving derivation for NER.

> **Execution Timing & Canonical Policy:**
> Preprocessing is dataset-scoped, canonical and immutable for `preprocessing_version="1.0.0"`. It executes once for a dataset when the preprocessing stage is run (Phase 3), before NLP analysis. Subsequent `AnalysisRuns` reuse the canonical preprocessed representations rather than overwriting them. For v1, preprocessing configuration is fixed and versioned rather than configurable independently for each AnalysisRun. This preserves reproducibility without coupling Phase 2 dataset ingestion to Phase 3 NLP preprocessing.

### Tasks

| # | Task | Files |
|---|------|-------|
| 3.1 | Create text cleaner module | `backend/app/nlp/preprocessing/text_cleaner.py` |
| 3.2 | Implement URL extraction/removal and normalization | (in text_cleaner.py) |
| 3.3 | Implement mention normalization (@user for sentiment; @user/removed for cleaned) | (in text_cleaner.py) |
| 3.4 | Implement hashtag extraction (preserve separately; strip `#` from cleaned text) | (in text_cleaner.py) |
| 3.5 | Implement emoji handling (convert to text / remove) | (in text_cleaner.py) |
| 3.6 | Implement HTML entity decoding | (in text_cleaner.py) |
| 3.7 | Implement whitespace/punctuation normalization | (in text_cleaner.py) |
| 3.8 | Implement case normalization (lowercased exclusively for `cleaned_text`) | (in text_cleaner.py) |
| 3.9 | Implement duplicate detection (hash-based) | (in text_cleaner.py) |
| 3.10 | Create sentiment-model-aligned text variant (`sentiment_ready_text` with `@user` and `http`) | (in text_cleaner.py) |
| 3.11 | Implement `derive_ner_text` (case-preserved, clean text derived deterministically at runtime from `original_text`) | (in text_cleaner.py) |
| 3.12 | Alembic migration: add preprocessing columns to posts and `preprocessing_version` to datasets | `migrations/versions/002_preprocessing.py` |
| 3.13 | Create canonical preprocessing service (dataset-level, immutable per run) | `backend/app/nlp/preprocessing/__init__.py` |
| 3.14 | Write comprehensive preprocessing tests (including task-specific representations) | `backend/tests/test_nlp/test_preprocessing.py` |

### Acceptance Criteria

- [ ] URLs are extracted and removed from `cleaned_text`, replaced with `http` in `sentiment_ready_text`.
- [ ] Mentions are extracted; `sentiment_ready_text` has `@user`.
- [ ] Hashtags are extracted into a list; `#` prefix removed from `cleaned_text` but word kept.
- [ ] Emojis are handled (configurable: convert or remove).
- [ ] Whitespace normalized; excessive punctuation reduced.
- [ ] `original_text` is preserved untouched.
- [ ] `cleaned_text` (lowercased) and `sentiment_ready_text` (case-preserved) stored in the database.
- [ ] `derive_ner_text` deterministically produces case-preserved text for NER without database storage.
- [ ] Preprocessing is canonical at the dataset level; distinct `AnalysisRuns` do not mutate `posts` preprocessing columns.
- [ ] Duplicate detection works and flags duplicates.
- [ ] All preprocessing tests pass with edge cases (empty text, emoji-only, URL-only, etc.).

### Verification Commands

```bash
cd backend
pytest tests/test_nlp/test_preprocessing.py -v
```

### Out of Scope

- Sentiment analysis (Phase 4).
- Topic modeling (Phase 5).

---

## Phase 4 — Sentiment Analysis

**Objective:** Integrate the `cardiffnlp/twitter-roberta-base-sentiment-latest` model (CC-BY-4.0) for batch sentiment classification, establish the AnalysisRun lifecycle, and implement concurrency control.

### Tasks

| # | Task | Files |
|---|------|-------|
| 4.1 | Create sentiment analyzer module using `cardiffnlp/twitter-roberta-base-sentiment-latest` (License: CC-BY-4.0, ~124M tweets training) | `backend/app/nlp/sentiment/analyzer.py` |
| 4.2 | Implement batch inference on `sentiment_ready_text` with configurable batch size | (in analyzer.py) |
| 4.3 | Alembic migration: create `analysis_runs`, `sentiment_results` tables with `created_at`, nullable `started_at`/`completed_at`, and `PortableJSON` | `migrations/versions/003_sentiment.py` |
| 4.4 | Create AnalysisRun model (with `created_at`, nullable `started_at`, nullable `completed_at`) | `backend/app/models/analysis.py` |
| 4.5 | Create SentimentResult model (1:N with Post across runs; `UNIQUE (post_id, analysis_run_id)`) | `backend/app/models/sentiment.py` |
| 4.6 | Create Pydantic schemas | `backend/app/schemas/analysis.py`, `backend/app/schemas/sentiment.py` |
| 4.7 | Create analysis service (run trigger, concurrency guard, status tracking) | `backend/app/services/analysis_service.py` |
| 4.8 | Create API endpoints: trigger analysis, get status | `backend/app/api/v1/analysis.py` |
| 4.9 | Implement background task execution (single-machine demo architecture; max 1 active analysis run, returns 409 if busy) | (in analysis_service.py) |
| 4.10 | Implement conditional evaluation metrics (when ground-truth exists) | `backend/app/nlp/sentiment/evaluator.py` |
| 4.11 | Write sentiment module tests | `backend/tests/test_nlp/test_sentiment.py` |
| 4.12 | Write analysis API tests (including concurrency conflict test) | `backend/tests/test_api/test_analysis.py` |

### Acceptance Criteria

- [ ] Sentiment model downloads and loads lazily on first use.
- [ ] Model uses `sentiment_ready_text` input.
- [ ] Batch inference works on 100+ posts.
- [ ] Each post gets: `label`, `confidence`, `score_positive`, `score_neutral`, `score_negative`.
- [ ] Results stored in `sentiment_results` table with unique constraint per post + analysis run.
- [ ] `POST /api/v1/analysis/run` records `created_at`, leaves `started_at` as NULL until worker starts.
- [ ] Concurrency guard rejects parallel analysis runs with HTTP 409 Conflict.
- [ ] `GET /api/v1/analysis/{run_id}/status` returns progress percentage and current step.
- [ ] Analysis run tracks status: `pending` → `running` (stamps `started_at`) → `completed` (stamps `completed_at`) / `failed`.
- [ ] If ground-truth sentiment column exists, evaluation metrics are computed (not fabricated).
- [ ] Tests pass (including multi-run post isolation test).

### Verification Commands

```bash
cd backend
pytest tests/test_nlp/test_sentiment.py -v
pytest tests/test_api/test_analysis.py -v
```

### Out of Scope

- Topic modeling (Phase 5).
- Dashboard display (Phase 9).

---

## Phase 5 — Topic Modeling

**Objective:** Implement BERTopic-based topic discovery using Sentence Transformer embeddings (`all-MiniLM-L6-v2`), UMAP (`random_state=42`), HDBSCAN, and c-TF-IDF, initialized with `nr_topics=None`.

### Tasks

| # | Task | Files |
|---|------|-------|
| 5.1 | Create topic modeler module | `backend/app/nlp/topics/modeler.py` |
| 5.2 | Implement embedding generation (`all-MiniLM-L6-v2`, batch size 64) | (in modeler.py or separate embedder) |
| 5.3 | Configure UMAP (`random_state=42`) + HDBSCAN + BERTopic (`nr_topics=None` to preserve natural clusters) | (in modeler.py) |
| 5.4 | Implement topic naming from top keywords | (in modeler.py) |
| 5.5 | Handle outlier topics (topic_id = −1) | (in modeler.py) |
| 5.6 | Alembic migration: create `topics`, `post_topics` tables | `migrations/versions/004_topics.py` |
| 5.7 | Create Topic and PostTopic models | `backend/app/models/topic.py` |
| 5.8 | Create Pydantic schemas | `backend/app/schemas/topic.py` |
| 5.9 | Integrate topic modeling into the analysis pipeline | (update `analysis_service.py`) |
| 5.10 | Write topic modeling tests | `backend/tests/test_nlp/test_topics.py` |

### Acceptance Criteria

- [ ] BERTopic discovers topics from `cleaned_text` without forcing topic reduction (`nr_topics=None`).
- [ ] UMAP uses `random_state=42` for deterministic cluster discovery.
- [ ] Each topic has: display_name, keywords (with scores), representative docs, post count.
- [ ] Outlier/unclassified posts are preserved as topic_id = −1.
- [ ] Results stored in `topics` and `post_topics` tables.
- [ ] Tests pass.

### Verification Commands

```bash
cd backend
pytest tests/test_nlp/test_topics.py -v
```

### Out of Scope

- Keyword trending analysis (Phase 6).
- Trend scoring (Phase 7).

---

## Phase 6 — NLP Enrichment (Keywords, Hashtags, NER)

**Objective:** Extract keywords, hashtag analytics, and named entities (using case-preserved text) from the analyzed posts.

### Tasks

| # | Task | Files |
|---|------|-------|
| 6.1 | Create keyword extractor module | `backend/app/nlp/keywords/extractor.py` |
| 6.2 | Implement corpus-level TF-IDF keyword extraction | (in extractor.py) |
| 6.3 | Implement hashtag frequency + growth computation | (in extractor.py) |
| 6.4 | Create NER module using spaCy `en_core_web_sm` operating on case-preserved runtime text | `backend/app/nlp/entities/recognizer.py` |
| 6.5 | Implement entity deduplication and aggregation | (in recognizer.py) |
| 6.6 | Alembic migration: create `entities`, `post_entities`, `keyword_snapshots` | `migrations/versions/005_entities_keywords.py` |
| 6.7 | Create Entity, PostEntity, KeywordSnapshot models | `backend/app/models/entity.py` |
| 6.8 | Create Pydantic schemas | `backend/app/schemas/entity.py` |
| 6.9 | Integrate into analysis pipeline | (update `analysis_service.py`) |
| 6.10 | Write keyword and NER tests (verifying case-preservation for NER) | `backend/tests/test_nlp/test_keywords.py`, `test_entities.py` |

### Acceptance Criteria

- [ ] Top-N keywords extracted per topic and globally.
- [ ] Hashtag frequency and growth calculated.
- [ ] spaCy NER extracts PERSON, ORG, GPE, PRODUCT, EVENT entities from case-preserved text.
- [ ] Entities are deduplicated (case-insensitive) and frequency-counted.
- [ ] All results stored in the database.
- [ ] Tests pass.

### Verification Commands

```bash
cd backend
pytest tests/test_nlp/test_keywords.py tests/test_nlp/test_entities.py -v
```

### Out of Scope

- Trend scoring (Phase 7).
- Dashboard visualization (Phase 9).

---

## Phase 7 — Trend Detection Engine

**Objective:** Implement UTC temporal aggregation, centered logistic normalization momentum scoring, recency modulation, and standard-deviation-based trend explanations, verified against deterministic unit-test scenarios.

### Tasks

| # | Task | Files |
|---|------|-------|
| 7.1 | Create temporal aggregation module operating strictly on UTC timestamps | `backend/app/nlp/trends/temporal.py` |
| 7.2 | Implement time-window bucketing (hourly/daily/weekly) with UTC boundary alignment | (in temporal.py) |
| 7.3 | Implement window comparison logic | (in temporal.py) |
| 7.4 | Create trend scorer with centered logistic normalization for volume growth, engagement growth, velocity, and burstiness z-score | `backend/app/nlp/trends/scorer.py` |
| 7.5 | Implement recency modulation factor (modulating momentum around neutral 0.50) | (in scorer.py) |
| 7.6 | Implement trend classification (Emerging/Rising/Stable/Declining) ensuring zero growth classifies as Stable | (in scorer.py) |
| 7.7 | Create trend explanation generator (describing burstiness in standard deviations above/below baseline) | `backend/app/nlp/trends/explainer.py` |
| 7.8 | Handle edge cases: zero baseline, division-by-zero, missing engagement redistribution (distinguishing unavailable engagement from genuine zero engagement), tiny samples | (in scorer.py) |
| 7.9 | Create TrendConfig dataclass | `backend/app/nlp/trends/config.py` |
| 7.10 | Alembic migration: create `trend_snapshots` table with UTC window columns | `migrations/versions/006_trends.py` |
| 7.11 | Create TrendSnapshot model | `backend/app/models/trend.py` |
| 7.12 | Create Pydantic schemas | `backend/app/schemas/trend.py` |
| 7.13 | Integrate into analysis pipeline | (update `analysis_service.py`) |
| 7.14 | Implement deterministic trend scoring unit-test scenarios | `backend/tests/test_nlp/test_trends.py` |

### Acceptance Criteria & Deterministic Test Scenarios

- [ ] Temporal aggregation strictly enforces UTC timezone and buckets posts along UTC calendar boundaries.
- [ ] Centered logistic normalization maps zero growth/velocity/burstiness to exactly 0.50 (neutral).
- [ ] Recency acts strictly as a modulation/relevance factor: $\text{TrendScore} = 0.5 + (M_{\text{base}} - 0.5) \cdot R$.
- [ ] Trend explanations describe burstiness as "X standard deviations above/below historical baseline" (never as a multiplicative ratio).
- [ ] **Deterministic Unit-Test Scenario 1 (No-Growth Case):** Zero volume growth, zero engagement change, zero velocity, normal historical baseline ($z=0$), latest post is recent ($R=1.0$) $\implies M_{\text{base}} = 0.50$, $\text{TrendScore} = 0.50$, classified unambiguously as **Stable** (NOT Rising).
- [ ] **Deterministic Unit-Test Scenario 2 (Rising Case):** Significant positive volume growth ($+150\%$), positive engagement growth, positive velocity, burst z-score $> 2.0$, recent post $\implies \text{TrendScore} \ge 0.60$, classified as **Rising**.
- [ ] **Deterministic Unit-Test Scenario 3 (Declining Case):** Negative volume growth ($-60\%$), negative engagement growth, negative velocity $\implies \text{TrendScore} < 0.40$, classified as **Declining**.
- [ ] **Deterministic Unit-Test Scenario 4 (Emerging-from-Zero Case):** Previous volume = 0, current volume $\ge \text{min\_posts}$ (e.g., 25 posts), positive velocity, recent post $\implies$ safe baseline division via $\text{min\_baseline}$, classified as **Emerging**.
- [ ] **Deterministic Unit-Test Scenario 5A (Missing Engagement Case — Fields Unavailable):** Engagement fields are not supplied / unmapped in the dataset $\implies$ engagement signal is omitted ($w_{\text{eng}} = 0$) and its weight is redistributed proportionally across volume, velocity, and burstiness; score computes cleanly without error or fabricating missing metrics.
- [ ] **Deterministic Unit-Test Scenario 5B (Genuine Zero Engagement Case — Fields Available):** Engagement fields are present/mapped in the dataset but all values are zero (`likes=0, comments=0, shares=0`) $\implies$ zero is treated as a valid measurement, engagement signal remains active ($e_g = 0 \implies S(0) = 0.50$), engagement weight is NOT redistributed.
- [ ] **Deterministic Unit-Test Scenario 6 (Tiny-Sample Case):** Total posts in topic $< \text{min\_posts\_for_trend}$ (e.g., 1–2 posts) $\implies$ division guarded, low-confidence flag set, avoided spurious Rising/Emerging classification.
- [ ] All trend scoring tests pass.

### Verification Commands

```bash
cd backend
pytest tests/test_nlp/test_trends.py -v
```

### Out of Scope

- API exposure (Phase 8).
- Dashboard (Phase 9).

---

## Phase 8 — Analytics APIs

**Objective:** Create all REST API endpoints that expose the pre-computed NLP results for the frontend dashboard.

### Tasks

| # | Task | Files |
|---|------|-------|
| 8.1 | Create dashboard service (aggregate queries) | `backend/app/services/dashboard_service.py` |
| 8.2 | Create search service | `backend/app/services/search_service.py` |
| 8.3 | Create dashboard API endpoints | `backend/app/api/v1/dashboard.py` |
| 8.4 | Create topics API endpoints (list + detail) | `backend/app/api/v1/topics.py` |
| 8.5 | Create trends API endpoints | `backend/app/api/v1/trends.py` |
| 8.6 | Create search API endpoints | `backend/app/api/v1/search.py` |
| 8.7 | Create pipeline info endpoint | `backend/app/api/v1/pipeline.py` |
| 8.8 | Create all Pydantic response schemas | `backend/app/schemas/dashboard.py` |
| 8.9 | Implement query parameter filtering (date, platform, keyword) | (in services + endpoints) |
| 8.10 | Write API tests for all endpoints | `backend/tests/test_api/` |

### Acceptance Criteria

- [ ] All dashboard endpoints return correctly structured JSON.
- [ ] Topic detail endpoint returns full trend analysis data.
- [ ] Search endpoint supports keyword, platform, date filters.
- [ ] Pipeline info endpoint returns model names, versions, parameters.
- [ ] Endpoints read from pre-computed DB tables (no live NLP inference).
- [ ] Pagination works (limit/offset).
- [ ] All API tests pass.

### Verification Commands

```bash
cd backend
pytest tests/test_api/ -v
# Manual: test each endpoint with curl/httpie
```

### Out of Scope

- Frontend (Phase 9).
- Trend detail page (Phase 10).

---

## Phase 9 — Dashboard

**Objective:** Build the main analytics dashboard with all visualizations.

### Tasks

| # | Task | Files |
|---|------|-------|
| 9.1 | Create TypeScript types matching API schemas | `frontend/src/lib/types.ts` |
| 9.2 | Create API client hooks | `frontend/src/hooks/useDashboard.ts` |
| 9.3 | Build Summary Cards component | `frontend/src/components/dashboard/SummaryCards.tsx` |
| 9.4 | Build Trending Topics Table | `frontend/src/components/dashboard/TrendingTopicsTable.tsx` |
| 9.5 | Build Activity Timeline chart (Recharts) | `frontend/src/components/dashboard/ActivityTimeline.tsx` |
| 9.6 | Build Sentiment Distribution chart | `frontend/src/components/dashboard/SentimentChart.tsx` |
| 9.7 | Build Trending Hashtags component | `frontend/src/components/dashboard/HashtagCloud.tsx` |
| 9.8 | Build Trending Keywords component | `frontend/src/components/dashboard/KeywordList.tsx` |
| 9.9 | Build Entity List component | `frontend/src/components/dashboard/EntityList.tsx` |
| 9.10 | Build Platform Distribution chart | `frontend/src/components/dashboard/PlatformDistribution.tsx` |
| 9.11 | Build Recent Posts panel | `frontend/src/components/dashboard/RecentPosts.tsx` |
| 9.12 | Assemble Dashboard page | `frontend/src/app/dashboard/page.tsx` |
| 9.13 | Build Dataset page (complete) | `frontend/src/app/datasets/page.tsx` |
| 9.14 | Build Analysis/Pipeline page | `frontend/src/app/analysis/page.tsx` |
| 9.15 | Implement loading, empty, and error states | (all components) |
| 9.16 | Implement responsive desktop layout | (all components) |
| 9.17 | Update sidebar navigation | `frontend/src/components/layout/Sidebar.tsx` |

### Acceptance Criteria

- [ ] Dashboard shows summary cards with real data from the API.
- [ ] Trending topics table shows topic name, trend score, change %, sentiment, volume, direction.
- [ ] Activity timeline renders a line/area chart.
- [ ] Sentiment chart shows positive/neutral/negative distribution.
- [ ] Hashtags, keywords, and entities are displayed.
- [ ] Platform distribution chart works.
- [ ] Loading spinners shown while data is fetching.
- [ ] Empty states shown when no data exists.
- [ ] Error states shown on API failures.
- [ ] Layout is clean and data-focused (not a generic SaaS landing page).
- [ ] `npm run build` succeeds.

### Verification Commands

```bash
cd frontend
npm run lint
npm run build
npm run dev
# Manual: verify dashboard with sample data via browser
```

### Out of Scope

- Trend detail/investigation page (Phase 10).
- Search/filter functionality (Phase 10).
- End-to-end tests (Phase 11).

---

## Phase 10 — Trend Investigation & Search

**Objective:** Build the topic/trend detail page and the search/filter functionality.

### Tasks

| # | Task | Files |
|---|------|-------|
| 10.1 | Build Topic Detail page | `frontend/src/app/topics/[id]/page.tsx` |
| 10.2 | Build TopicDetail component (header + explanation) | `frontend/src/components/topics/TopicDetail.tsx` |
| 10.3 | Build topic volume timeline | `frontend/src/components/topics/TopicTimeline.tsx` |
| 10.4 | Build topic sentiment timeline | `frontend/src/components/topics/SentimentTimeline.tsx` |
| 10.5 | Build topic keywords + hashtags panel | (in TopicDetail) |
| 10.6 | Build topic entities panel | (in TopicDetail) |
| 10.7 | Build topic representative posts panel | (in TopicDetail) |
| 10.8 | Build topic engagement statistics | (in TopicDetail) |
| 10.9 | Build Search page with filters | `frontend/src/app/search/page.tsx` |
| 10.10 | Implement keyword, topic, platform, date filters | (in Search page) |
| 10.11 | Create useTopic and useSearch hooks | `frontend/src/hooks/useTopics.ts`, `useSearch.ts` |
| 10.12 | Make trending topics table rows clickable → navigate to detail | (update TrendingTopicsTable) |

### Acceptance Criteria

- [ ] Clicking a topic from the dashboard navigates to the detail page.
- [ ] Detail page shows: topic name, trend score, status badge, explanation, keywords, hashtags, representative posts, volume timeline, sentiment timeline, entities, engagement stats.
- [ ] Trend explanation is clearly visible and derived from real statistics.
- [ ] Search page filters posts by keyword, platform, and date range.
- [ ] All navigation works (back to dashboard, between topics).

### Verification Commands

```bash
cd frontend
npm run lint
npm run build
# Manual: verify trend detail page and search via browser
```

### Out of Scope

- Evaluation metrics page (Phase 11).
- End-to-end tests (Phase 11).

---

## Phase 11 — Evaluation & Testing

**Objective:** Add model evaluation metrics, comprehensive tests, and end-to-end verification.

### Tasks

| # | Task | Files |
|---|------|-------|
| 11.1 | Implement evaluation metrics display on Analysis page | (update Analysis page) |
| 11.2 | Display confusion matrix if ground-truth exists | (Analysis page component) |
| 11.3 | Display dataset statistics on Analysis page | (Analysis page component) |
| 11.4 | Display preprocessing statistics | (Analysis page component) |
| 11.5 | Display topic statistics | (Analysis page component) |
| 11.6 | Create `MODEL_EVALUATION.md` | `docs/MODEL_EVALUATION.md` |
| 11.7 | Write backend integration tests (full pipeline) | `backend/tests/test_integration/` |
| 11.8 | Write frontend component tests | `frontend/src/__tests__/` |
| 11.9 | Write Playwright E2E tests (upload → analyze → dashboard) | `frontend/e2e/` |
| 11.10 | Run full test suite and fix issues | |
| 11.11 | Verify complete flow: start app → load sample data → run analysis → explore dashboard → investigate trend | |

### Acceptance Criteria

- [ ] Analysis page shows actual pipeline diagram, model info, and statistics.
- [ ] Evaluation metrics shown only when ground-truth labels exist.
- [ ] No fabricated metrics or scores.
- [ ] Backend test coverage ≥ 70% for NLP and trend logic.
- [ ] At least 1 E2E test covers the critical path.
- [ ] Full pipeline runs end-to-end with sample data.

### Verification Commands

```bash
cd backend
pytest tests/ -v --cov=app --cov-report=term-missing
cd frontend
npm test
npx playwright test
```

### Out of Scope

- Documentation polish (Phase 12).

---

## Phase 12 — Documentation & Academic Polish

**Objective:** Complete all documentation, create the project report support materials, and ensure the project is demo-ready.

### Tasks

| # | Task | Files |
|---|------|-------|
| 12.1 | Write comprehensive README.md | `README.md` |
| 12.2 | Create PROJECT_REPORT_NOTES.md | `docs/PROJECT_REPORT_NOTES.md` |
| 12.3 | Finalize MODEL_EVALUATION.md with actual results | `docs/MODEL_EVALUATION.md` |
| 12.4 | Add architecture diagram images | `docs/diagrams/` |
| 12.5 | Add screenshots of dashboard to README | `docs/screenshots/` |
| 12.6 | Document installation + run instructions | (in README) |
| 12.7 | Document dataset format requirements | (in README) |
| 12.8 | Document trend scoring algorithm | (in README) |
| 12.9 | Document limitations and future scope | (in README) |
| 12.10 | Final code review and cleanup | |
| 12.11 | Verify fresh install + demo flow from scratch | |

### Acceptance Criteria

- [ ] README covers: objective, problem statement, NLP techniques, architecture, installation, dataset format, running, models, trend algorithm, screenshots, limitations, future scope.
- [ ] PROJECT_REPORT_NOTES.md has structured notes for college report/PPT/viva preparation.
- [ ] Fresh clone → install → run → demo works without errors.
- [ ] All documentation is accurate (no stale references).
- [ ] Screenshots are current.

### Verification

```bash
# Simulate fresh setup
git clone <repo> && cd social-trend-analyzer
# Follow README instructions
# Verify demo works end-to-end
```

---

## Git Branch Strategy

| Phase | Branch Name |
|-------|------------|
| 1 | `phase-1-foundation` |
| 2 | `phase-2-data-ingestion` |
| 3 | `phase-3-nlp-preprocessing` |
| 4 | `phase-4-sentiment` |
| 5 | `phase-5-topic-modeling` |
| 6 | `phase-6-nlp-enrichment` |
| 7 | `phase-7-trend-detection` |
| 8 | `phase-8-analytics-apis` |
| 9 | `phase-9-dashboard` |
| 10 | `phase-10-trend-investigation` |
| 11 | `phase-11-evaluation-testing` |
| 12 | `phase-12-documentation` |

Each phase merges into `main` upon completion and verification.
