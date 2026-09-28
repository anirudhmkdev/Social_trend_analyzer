# Social Trend Analyzer — Architecture Document

> **Version:** 1.0  
> **Date:** 2026-08-09  
> **Status:** Draft — Awaiting Review  

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js)                          │
│  ┌──────────┐ ┌───────────┐ ┌──────────┐ ┌───────────┐ ┌────────┐ │
│  │Dashboard │ │Trend      │ │Dataset   │ │Analysis/  │ │Search/ │ │
│  │Page      │ │Detail Page│ │Page      │ │Pipeline Pg│ │Filter  │ │
│  └────┬─────┘ └─────┬─────┘ └────┬─────┘ └─────┬─────┘ └───┬────┘ │
│       └──────────────┴────────────┴─────────────┴───────────┘      │
│                              │ REST API calls                      │
└──────────────────────────────┼──────────────────────────────────────┘
                               │
┌──────────────────────────────┼──────────────────────────────────────┐
│                     BACKEND (FastAPI)                               │
│  ┌───────────────────────────┼───────────────────────────────────┐  │
│  │                    API Layer (Routers)                        │  │
│  │  /datasets  /analysis  /dashboard  /topics  /trends /search  │  │
│  └───────────────────────────┬───────────────────────────────────┘  │
│                              │                                      │
│  ┌───────────────────────────┼───────────────────────────────────┐  │
│  │                   Service Layer                               │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │  │
│  │  │Ingestion │ │NLP       │ │Analytics │ │Trend Detection   │ │  │
│  │  │Service   │ │Orchestr. │ │Service   │ │Engine            │ │  │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────────┬─────────┘ │  │
│  └───────┼────────────┼────────────┼─────────────────┼───────────┘  │
│          │            │            │                 │               │
│  ┌───────┼────────────┼────────────┼─────────────────┼───────────┐  │
│  │       │      NLP Pipeline       │                 │           │  │
│  │  ┌────▼─────┐ ┌────▼─────┐ ┌────▼─────┐ ┌───────▼────────┐  │  │
│  │  │Preprocess│ │Sentiment │ │Topic     │ │Keyword/Hashtag │  │  │
│  │  │Module    │ │Module    │ │Module    │ │Module          │  │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └────────────────┘  │  │
│  │  ┌──────────┐ ┌──────────┐                                  │  │
│  │  │NER       │ │Temporal  │                                  │  │
│  │  │Module    │ │Aggregator│                                  │  │
│  │  └──────────┘ └──────────┘                                  │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                              │                                      │
│  ┌───────────────────────────┼───────────────────────────────────┐  │
│  │                    Data Layer (SQLAlchemy)                    │  │
│  │  Models / Repositories / Migrations                          │  │
│  └───────────────────────────┬───────────────────────────────────┘  │
└──────────────────────────────┼──────────────────────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │   PostgreSQL / SQLite│
                    └─────────────────────┘
```

---

## 2. Technology Stack

### 2.1 Frontend

| Technology | Version | Purpose |
|-----------|---------|---------|
| Next.js | 15.x (security-patched) | React framework with App Router (pinned in `package-lock.json`) |
| TypeScript | 5.x | Type safety (strict mode) |
| Tailwind CSS | 4.x | Utility-first styling |
| shadcn/ui | latest compatible | Pre-built accessible UI components |
| Recharts | 2.x | Data visualization / charting |
| Lucide React | latest | Icon library |
| Axios / fetch | — | HTTP client for API calls |

> **Frontend Reproducibility:** An active, supported, security-patched Next.js 15 version is resolved at implementation initialization. The exact resolved versions of all packages and transitive dependencies are locked into a committed `frontend/package-lock.json`.

### 2.2 Backend

| Technology | Version | Purpose |
|-----------|---------|---------|
| Python | 3.11–3.12 | Runtime |
| FastAPI | 0.115+ | Web framework with Pydantic v2 |
| Pydantic | 2.x | Schema validation & serialization |
| SQLAlchemy | 2.x | ORM and database toolkit |
| Alembic | 1.x | Database migrations |
| Uvicorn | 0.30+ | ASGI server |
| python-multipart | latest | File upload handling |

> **Backend Dependency Management:** To prevent dependency drift, the project maintains a **single source of truth** for Python dependencies (`pyproject.toml` or `requirements.in`). Exact resolved versions are locked into a committed `backend/requirements.lock` (compiled via `pip-compile` / `uv pip compile`). Evaluators install directly from the lockfile.

### 2.3 NLP / Data Science

| Technology | Version | Purpose |
|-----------|---------|---------|
| pandas | 2.x | Data manipulation |
| NumPy | 1.x / 2.x | Numerical computing |
| scikit-learn | 1.x | TF-IDF, CountVectorizer |
| spaCy | 3.8.x | NER (case-preserved text) |
| en_core_web_sm | 3.8.x | spaCy English model (lightweight, ~12MB) |
| transformers | 4.x | Hugging Face transformer inference |
| sentence-transformers | 3.x | Dense sentence embeddings (`all-MiniLM-L6-v2`) |
| BERTopic | 0.17.x | Topic modeling (`nr_topics=None`) |
| UMAP-learn | 0.5.x | Dimensionality reduction (`random_state=42`) |
| hdbscan | 0.8.x | Density-based clustering |
| torch | 2.x | PyTorch backend (CPU-only build) |

### 2.4 Database

| Technology | Purpose |
|-----------|---------|
| PostgreSQL 15+ | Primary production database |
| SQLite | Optional fallback for simple dev/testing |

### 2.5 Testing

| Technology | Purpose |
|-----------|---------|
| pytest | Backend unit and integration tests |
| pytest-asyncio | Async test support |
| httpx | API testing with FastAPI TestClient |
| Jest + React Testing Library | Frontend component tests |
| Playwright | End-to-end browser tests |

### 2.6 Dev Tools

| Technology | Purpose |
|-----------|---------|
| Ruff | Python linting + formatting |
| mypy | Python type checking |
| ESLint | TypeScript/JS linting |
| Prettier | Frontend formatting |

---

## 3. System Architecture

### 3.1 Separation of Concerns

The system follows a strict **layered architecture**:

```
┌──────────────────────────┐
│     Presentation Layer   │  Next.js frontend
├──────────────────────────┤
│     API Layer            │  FastAPI routers (thin controllers)
├──────────────────────────┤
│     Service Layer        │  Business logic orchestration
├──────────────────────────┤
│     NLP Layer            │  Independent NLP modules
├──────────────────────────┤
│     Data Access Layer    │  SQLAlchemy models, repositories
├──────────────────────────┤
│     Database             │  PostgreSQL / SQLite
└──────────────────────────┘
```

**Key constraints:**
- NLP code MUST NOT appear in API route handlers.
- Trend scoring MUST NOT appear in frontend components.
- Frontend consumes only REST API contracts (Pydantic-serialized JSON).
- Each NLP module is independently testable and replaceable.

### 3.2 Communication Patterns

| From | To | Mechanism |
|------|----|-----------|
| Frontend | Backend | REST API (JSON over HTTP) |
| API Layer | Service Layer | Direct function calls (dependency injection) |
| Service Layer | NLP Layer | Direct function calls (sync; wrapped in background tasks for long-running jobs) |
| Service Layer | Data Layer | SQLAlchemy session |
| NLP Modules | Each Other | Data passed via service layer (no direct cross-module calls) |

### 3.3 Long-Running NLP Jobs & Concurrency Architecture

NLP processing (especially sentence transformer embedding generation and sentiment classification on large datasets) can take several minutes on CPU. The architecture handles this with an asynchronous lifecycle:

1. **API receives analysis request** → creates an `AnalysisRun` record with status `PENDING`, sets `created_at`, leaving `started_at` as `NULL`.
2. **Background task** (FastAPI `BackgroundTasks`) is spawned to execute the NLP pipeline. When the worker thread picks up the job, `started_at` is set to the current UTC timestamp and status changes to `RUNNING`.
3. **Status polling endpoint** (`GET /api/v1/analysis/{run_id}/status`) lets the frontend display progress percentage and current pipeline step.
4. **On completion or failure**, results are written to the database, `completed_at` is stamped in UTC, and status becomes `COMPLETED` or `FAILED`.
5. **Dashboard endpoints** read strictly from pre-computed database tables, never triggering live NLP inference.

```
Client                    API                   Background Worker
  │─── POST /analysis ──▶│                          │
  │◀── 202 {run_id} ─────│── spawn task ──────────▶│ (sets started_at)
  │                       │                          │── preprocessing check
  │─── GET /analysis/     │                          │── embeddings
  │     {run_id}/status ─▶│◀─ read DB status ───────│── topic modeling (nr_topics=None)
  │◀── {progress: 55%} ──│                          │── sentiment (sentiment_ready_text)
  │                       │                          │── NER (case-preserved)
  │─── GET /analysis/     │                          │── temporal aggregation (UTC)
  │     {run_id}/status ─▶│◀─ read DB status ───────│── trend detection (logistic momentum)
  │◀── {status: done} ───│                          │── COMPLETED (sets completed_at)
  │                       │                          │
  │─── GET /dashboard ──▶│                          │
  │◀── {cached results} ─│                          │
```

> [!WARNING]
> **Single-Machine Demo Architecture Disclaimer:**
> FastAPI `BackgroundTasks` executes in-process on the local Uvicorn ASGI server. This is a lightweight single-machine demo architecture suitable for a college evaluation project; it is **NOT** a distributed or durable production job queue (such as Celery with Redis/RabbitMQ). If the Uvicorn process restarts while an analysis is in progress, the job will terminate and must be re-run.
> 
> **Concurrency Limiting:**
> To protect local CPU and memory resources from exhaustion, concurrent analysis runs are **strictly restricted**: only **one active analysis job** may execute at a time. The backend enforces this via an in-process lock / status check. Any request to trigger an analysis while another is `RUNNING` will return an `HTTP 409 Conflict` response with an explanatory message.

---

## 4. Directory Structure

```
social-trend-analyzer/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app factory
│   │   ├── config.py                  # Settings (Pydantic BaseSettings)
│   │   ├── dependencies.py            # DI helpers (get_db, etc.)
│   │   │
│   │   ├── api/                       # API Layer
│   │   │   ├── __init__.py
│   │   │   ├── router.py              # Root router aggregation
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── datasets.py        # Dataset upload/manage endpoints
│   │   │       ├── analysis.py        # Trigger/status endpoints
│   │   │       ├── dashboard.py       # Dashboard aggregate endpoints
│   │   │       ├── topics.py          # Topic list/detail endpoints
│   │   │       ├── trends.py          # Trend endpoints
│   │   │       └── search.py          # Search/filter endpoints
│   │   │
│   │   ├── core/                      # Cross-cutting concerns
│   │   │   ├── __init__.py
│   │   │   ├── exceptions.py          # Custom exceptions
│   │   │   └── logging.py            # Logging configuration
│   │   │
│   │   ├── database/                  # Data Access Layer
│   │   │   ├── __init__.py
│   │   │   ├── engine.py             # Engine/session factory
│   │   │   ├── base.py               # Declarative base
│   │   │   └── migrations/           # Alembic migrations
│   │   │       ├── env.py
│   │   │       ├── alembic.ini
│   │   │       └── versions/
│   │   │
│   │   ├── models/                    # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── dataset.py
│   │   │   ├── post.py
│   │   │   ├── analysis.py
│   │   │   ├── topic.py
│   │   │   ├── sentiment.py
│   │   │   ├── entity.py
│   │   │   └── trend.py
│   │   │
│   │   ├── schemas/                   # Pydantic schemas
│   │   │   ├── __init__.py
│   │   │   ├── dataset.py
│   │   │   ├── post.py
│   │   │   ├── analysis.py
│   │   │   ├── topic.py
│   │   │   ├── sentiment.py
│   │   │   ├── entity.py
│   │   │   ├── trend.py
│   │   │   └── dashboard.py
│   │   │
│   │   ├── services/                  # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── dataset_service.py
│   │   │   ├── analysis_service.py
│   │   │   ├── dashboard_service.py
│   │   │   └── search_service.py
│   │   │
│   │   ├── ingestion/                 # Data ingestion
│   │   │   ├── __init__.py
│   │   │   ├── csv_parser.py
│   │   │   ├── json_parser.py
│   │   │   ├── column_mapper.py
│   │   │   ├── validator.py
│   │   │   └── normalizer.py
│   │   │
│   │   └── nlp/                       # NLP Pipeline
│   │       ├── __init__.py
│   │       ├── pipeline.py            # Orchestrator
│   │       ├── preprocessing/
│   │       │   ├── __init__.py
│   │       │   └── text_cleaner.py
│   │       ├── sentiment/
│   │       │   ├── __init__.py
│   │       │   └── analyzer.py
│   │       ├── topics/
│   │       │   ├── __init__.py
│   │       │   └── modeler.py
│   │       ├── keywords/
│   │       │   ├── __init__.py
│   │       │   └── extractor.py
│   │       ├── entities/
│   │       │   ├── __init__.py
│   │       │   └── recognizer.py
│   │       └── trends/
│   │           ├── __init__.py
│   │           ├── temporal.py        # Time-window aggregation
│   │           ├── scorer.py          # TrendScore computation
│   │           └── explainer.py       # Human-readable explanations
│   │
│   ├── data/
│   │   └── sample_dataset.csv         # Bundled demo data
│   │
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_ingestion/
│   │   ├── test_nlp/
│   │   │   ├── test_preprocessing.py
│   │   │   ├── test_sentiment.py
│   │   │   ├── test_topics.py
│   │   │   ├── test_keywords.py
│   │   │   ├── test_entities.py
│   │   │   └── test_trends.py
│   │   ├── test_services/
│   │   └── test_api/
│   │
│   ├── pyproject.toml                 # Python project config
│   ├── requirements.lock              # Committed lockfile (pip-compile)
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── app/                       # Next.js App Router
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx               # Redirects to /dashboard
│   │   │   ├── dashboard/
│   │   │   │   └── page.tsx
│   │   │   ├── topics/
│   │   │   │   ├── page.tsx
│   │   │   │   └── [id]/
│   │   │   │       └── page.tsx       # Trend detail
│   │   │   ├── datasets/
│   │   │   │   └── page.tsx
│   │   │   ├── analysis/
│   │   │   │   └── page.tsx           # Pipeline/model info
│   │   │   └── search/
│   │   │       └── page.tsx
│   │   │
│   │   ├── components/
│   │   │   ├── ui/                    # shadcn/ui components
│   │   │   ├── layout/
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   ├── Header.tsx
│   │   │   │   └── AppShell.tsx
│   │   │   ├── dashboard/
│   │   │   │   ├── SummaryCards.tsx
│   │   │   │   ├── TrendingTopicsTable.tsx
│   │   │   │   ├── ActivityTimeline.tsx
│   │   │   │   ├── SentimentChart.tsx
│   │   │   │   ├── HashtagCloud.tsx
│   │   │   │   ├── KeywordList.tsx
│   │   │   │   ├── EntityList.tsx
│   │   │   │   └── PlatformDistribution.tsx
│   │   │   ├── topics/
│   │   │   │   ├── TopicDetail.tsx
│   │   │   │   └── TopicTimeline.tsx
│   │   │   ├── datasets/
│   │   │   │   ├── FileUpload.tsx
│   │   │   │   ├── ColumnMapper.tsx
│   │   │   │   ├── DataPreview.tsx
│   │   │   │   └── ValidationResults.tsx
│   │   │   └── analysis/
│   │   │       ├── PipelineDiagram.tsx
│   │   │       └── ModelInfo.tsx
│   │   │
│   │   ├── lib/
│   │   │   ├── api.ts                # API client
│   │   │   ├── types.ts              # TypeScript types matching Pydantic schemas
│   │   │   └── utils.ts              # Utility functions
│   │   │
│   │   └── hooks/
│   │       ├── useDashboard.ts
│   │       ├── useTopics.ts
│   │       └── useDatasets.ts
│   │
│   ├── public/
│   ├── package.json
│   ├── package-lock.json              # Committed frontend lockfile
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── next.config.ts
│   └── .env.local.example
│
├── docs/
│   ├── PRD.md
│   ├── ARCHITECTURE.md
│   ├── NLP_PIPELINE.md
│   ├── DATA_SCHEMA.md
│   ├── IMPLEMENTATION_ROADMAP.md
│   ├── MODEL_EVALUATION.md
│   └── PROJECT_REPORT_NOTES.md
│
├── .agents/
│   └── AGENTS.md
│
├── .gitignore
├── README.md
└── docker-compose.yml               # PostgreSQL for local dev (optional)
```

---

## 5. API Design

### 5.1 Endpoint Overview

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/v1/datasets/upload` | Upload CSV/JSON file |
| `POST` | `/api/v1/datasets/sample` | Load bundled sample dataset |
| `GET` | `/api/v1/datasets` | List all datasets |
| `GET` | `/api/v1/datasets/{id}` | Get dataset details |
| `GET` | `/api/v1/datasets/{id}/preview` | Preview dataset rows |
| `POST` | `/api/v1/datasets/{id}/map-columns` | Submit column mappings |
| `POST` | `/api/v1/datasets/{id}/validate` | Run validation |
| `DELETE` | `/api/v1/datasets/{id}` | Delete a dataset |
| | | |
| `POST` | `/api/v1/analysis/run` | Start NLP analysis |
| `GET` | `/api/v1/analysis/{run_id}/status` | Get analysis status/progress |
| `GET` | `/api/v1/analysis/{run_id}` | Get analysis run details |
| `GET` | `/api/v1/analysis` | List all analysis runs |
| | | |
| `GET` | `/api/v1/dashboard/summary` | Summary cards data |
| `GET` | `/api/v1/dashboard/timeline` | Activity timeline data |
| `GET` | `/api/v1/dashboard/sentiment` | Sentiment distribution |
| `GET` | `/api/v1/dashboard/hashtags` | Trending hashtags |
| `GET` | `/api/v1/dashboard/keywords` | Trending keywords |
| `GET` | `/api/v1/dashboard/entities` | Trending entities |
| `GET` | `/api/v1/dashboard/platforms` | Platform distribution |
| | | |
| `GET` | `/api/v1/topics` | List topics with trend info |
| `GET` | `/api/v1/topics/{id}` | Topic detail (full trend analysis) |
| `GET` | `/api/v1/topics/{id}/posts` | Posts for a topic |
| `GET` | `/api/v1/topics/{id}/timeline` | Topic volume/sentiment over time |
| | | |
| `GET` | `/api/v1/trends` | Ranked trending topics |
| `GET` | `/api/v1/trends/config` | Current trend scoring config |
| | | |
| `GET` | `/api/v1/search/posts` | Search/filter posts |
| `GET` | `/api/v1/pipeline/info` | NLP pipeline metadata |

### 5.2 Query Parameters (common)

| Parameter | Type | Description |
|-----------|------|-------------|
| `analysis_run_id` | UUID | Scope to a specific analysis run |
| `time_window` | enum | `hourly` / `daily` / `weekly` |
| `start_date` | datetime | Filter start |
| `end_date` | datetime | Filter end |
| `platform` | string | Filter by platform |
| `keyword` | string | Text search |
| `limit` | int | Pagination limit |
| `offset` | int | Pagination offset |

---

## 6. Database Architecture

See [DATA_SCHEMA.md](DATA_SCHEMA.md) for the complete entity-relationship diagram and table definitions.

### 6.1 Core Entities

```
Dataset ──< Post ──< SentimentResult (1:N across runs, unique per post_id + run_id)
                 ──< PostTopic >── Topic
                 ──< PostEntity >── Entity
                 
AnalysisRun ──< Topic
            ──< TrendSnapshot
            ──< AnalysisStep (progress tracking)
```

### 6.2 Design Principles

1. **Pre-computed results**: All NLP outputs (sentiment, topics, entities, trends) are stored in the database. The dashboard reads from these tables, never from live inference.
2. **Analysis run isolation**: Multiple analysis runs can exist for the same dataset; the dashboard shows the latest (or user-selected) run.
3. **Temporal snapshots**: `TrendSnapshot` captures trend scores at specific time windows in UTC, enabling trend-over-time visualization.
4. **Junction tables**: `PostTopic` and `PostEntity` support many-to-many relationships.

---

## 7. Deployment Architecture

### 7.1 Local Development

```
┌─────────────────┐     ┌─────────────────┐     ┌──────────────┐
│  Next.js Dev    │────▶│  FastAPI Dev     │────▶│ PostgreSQL   │
│  localhost:3000 │     │  localhost:8000  │     │ localhost:5432│
└─────────────────┘     └─────────────────┘     └──────────────┘
                                                       │
                                              (or SQLite file)
```

- **Frontend**: `npm run dev` on port 3000
- **Backend**: `uvicorn app.main:app --reload` on port 8000
- **Database**: PostgreSQL via Docker Compose, or SQLite for zero-setup testing

### 7.2 Optional Docker Compose

```yaml
services:
  db:
    image: postgres:16
    ports: ["5432:5432"]
    environment:
      POSTGRES_DB: social_trend_analyzer
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: dev
    volumes:
      - pgdata:/var/lib/postgresql/data
volumes:
  pgdata:
```

---

## 8. Security Considerations

| Concern | Mitigation |
|---------|------------|
| File upload abuse | Validate file type, size limits (50MB), content sniffing |
| SQL injection | SQLAlchemy ORM with parameterized queries |
| Secrets in code | `.env` for config; `.env.example` committed; `.env` in `.gitignore` |
| CORS | Configure allowed origins for local development |
| Data privacy | Sample data uses anonymized identifiers; no real user data stored |

---

## 9. Key Architectural Decisions

| Decision | Rationale |
|----------|-----------|
| **Monorepo** (backend/ + frontend/) | Simplifies development for a college project; single git repo. |
| **REST over WebSocket** for status | Polling-based status is simpler to implement and debug than WebSocket for a non-real-time system. |
| **Background tasks over Celery** | FastAPI BackgroundTasks is used as a single-machine demo architecture for college evaluation; avoids Redis/Celery complexity. Concurrency is strictly limited to 1 active run to protect local CPU/RAM. Not presented as a durable production queue. |
| **PostgreSQL + SQLite dual support** | PostgreSQL with native `JSONB` for proper deployments; SQLite with `JSON` fallback for zero-dependency quick demos via `PortableJSON = JSON().with_variant(JSONB(), "postgresql")`. |
| **Committed Lockfiles for Reproducibility** | Python dependencies use a single source of truth locked into committed `requirements.lock`; frontend dependencies are locked via committed `package-lock.json` with a security-patched Next.js 15. |
| **Canonical Dataset Preprocessing** | Preprocessing is dataset-scoped, canonical, and immutable for `preprocessing_version="1.0.0"`. It executes once when the preprocessing stage is run, before NLP analysis. Subsequent AnalysisRuns reuse these canonical representations without overwriting them, preserving reproducibility without coupling ingestion to preprocessing. |
| **spaCy `en_core_web_sm` (default)** | Significantly smaller download (~12MB vs ~500MB for `_trf`). Operates on case-preserved text derived at runtime. |
| **CPU-only inference** | GPU not assumed on evaluator machines; torch CPU is sufficient for <1000 posts. |
| **Pre-computed analytics** | Dashboard performance depends on cached DB results, not live NLP. |
| **API versioning (`/v1/`)** | Future-proofs the API surface without breaking clients. |
