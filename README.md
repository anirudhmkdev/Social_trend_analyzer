# Social Trend Analyzer

> **An NLP-Based Platform for Detecting Emerging Topics, Sentiment, and Trends from Social Media Text**

---

## 1. Project Overview

Social Trend Analyzer is a full-stack Natural Language Processing (NLP) application designed to ingest social-media post datasets and discover emerging topics, trending keywords/hashtags, sentiment dynamics, named entities, and temporal trends. Insights are pre-computed and surfaced through an interactive web dashboard.

---

## 2. Implementation Status: Phase 1 — Project Foundation

The project is structured according to the 10-phase roadmap defined in [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md).

- **Current Status:** **Phase 1 Complete (Foundation)**
- **Active Deliverables:**
  - FastAPI backend API framework with `/api/v1` versioning and `/api/v1/health` check
  - Pydantic v2 settings management with `.env` configuration
  - SQLAlchemy 2.x data access layer supporting PostgreSQL (primary) and SQLite (dev/testing fallback) with dialect-aware `PortableJSON = JSON().with_variant(JSONB(), "postgresql")`
  - Initial `Dataset` and `Post` database models with UUID primary keys and timezone-aware UTC timestamps
  - Alembic migration framework with verified `001_initial` migration
  - Next.js 15 App Router frontend with TypeScript strict mode, Tailwind CSS, and application shell (`Sidebar`, `Header`, `AppShell`)
  - Deterministic dependency lockfiles (`backend/requirements.lock` and `frontend/package-lock.json`)
  - Docker Compose configuration for local PostgreSQL service

> **Phase Boundary Notice:**  
> All NLP models (BERTopic, Sentence Transformers `all-MiniLM-L6-v2`, CardiffNLP Twitter-RoBERTa sentiment classifier, spaCy NER `en_core_web_sm`), dataset CSV ingestion, background analysis tasks, and dashboard analytics are **PLANNED** for Phases 2–10 and are **NOT** implemented in Phase 1.

---

## 3. Architecture Overview

```text
social-trend-analyzer/
├── backend/                  # FastAPI REST API & Processing Engine
│   ├── app/
│   │   ├── api/v1/           # Versioned route controllers (/health)
│   │   ├── core/             # Exceptions and logging
│   │   ├── database/         # Engine, declarative base, migrations
│   │   ├── models/           # SQLAlchemy ORM models (Dataset, Post)
│   │   ├── config.py         # Pydantic Settings
│   │   ├── dependencies.py   # Dependency injection (get_db)
│   │   └── main.py           # Application factory & CORS
│   ├── tests/                # Pytest suite with isolated SQLite fixture
│   ├── pyproject.toml        # Single Python dependency source of truth
│   ├── requirements.lock     # Committed pip-compile/uv lockfile
│   └── .env.example          # Environment template
│
├── frontend/                 # Next.js 15 Web Application
│   ├── src/
│   │   ├── app/              # App Router (layout, page)
│   │   ├── components/layout/# AppShell, Sidebar, Header
│   │   └── lib/              # API client (api.ts) & utils
│   ├── package.json          # Frontend dependencies
│   └── package-lock.json     # Committed npm lockfile
│
├── docs/                     # Specifications & Research Notes
├── docker-compose.yml        # Local PostgreSQL 16 service
├── .gitignore                # Workspace gitignore
└── README.md                 # Project documentation
```

---

## 4. Prerequisites

- **Python:** 3.11 or 3.12 (Python 3.12 recommended; `uv` or `python -m venv`)
- **Node.js:** v18+ or v20+ (v24 supported) with `npm`
- **Docker & Docker Compose:** Optional for local PostgreSQL (SQLite is supported out-of-the-box for zero-setup local dev)

---

## 5. Getting Started

### 5.1 Clone & Setup Environment

```bash
git clone https://github.com/anirudhmkdev/Social_trend_analyzer.git
cd Social_trend_analyzer
```

### 5.2 Database Setup (Optional PostgreSQL)

To start local PostgreSQL via Docker Compose:

```bash
docker compose up -d db
```

*Note: If Docker is not running, the application defaults to an embedded SQLite database (`sqlite:///./social_trend_analyzer.db`).*

---

### 5.3 Backend Setup

1. **Navigate to backend and create virtual environment:**
   ```bash
   cd backend
   python -m venv .venv
   # Windows PowerShell:
   .\.venv\Scripts\activate
   # Linux/macOS:
   # source .venv/bin/activate
   ```

2. **Install locked dependencies:**
   ```bash
   pip install -r requirements.lock
   # or with uv:
   # uv pip sync requirements.lock
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   ```

4. **Run database migrations:**
   ```bash
   alembic upgrade head
   ```

5. **Start backend development server:**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

6. **Verify health endpoint:**
   ```bash
   curl http://localhost:8000/api/v1/health
   # Expected response: {"status": "ok"}
   ```

---

### 5.4 Frontend Setup

1. **Navigate to frontend and install dependencies:**
   ```bash
   cd ../frontend
   npm ci
   ```

2. **Configure environment:**
   ```bash
   cp .env.local.example .env.local
   ```

3. **Start frontend development server:**
   ```bash
   npm run dev
   ```

4. Open [http://localhost:3000](http://localhost:3000) in your browser to view the application shell.

---

## 6. Verification & Quality Commands

### Backend Verification

```bash
cd backend

# Run linting
python -m ruff check app tests

# Run type checking
python -m mypy app --ignore-missing-imports

# Run tests
pytest tests -v

# Verify migration rollback and re-apply
alembic downgrade -1
alembic upgrade head
```

### Frontend Verification

```bash
cd frontend

# Run linting
npm run lint

# Run type check
npx tsc --noEmit

# Run production build
npm run build
```

---

## 7. Roadmap & Next Steps

- **Phase 2 (Next):** Dataset Ingestion (CSV upload, column mapper, validation, UTC normalization).
- **Phases 3–7:** Canonical Preprocessing, Sentiment Analysis, Topic Modeling, Keyword & Entity Extraction, Trend Detection Engine.
- **Phases 8–10:** Analytics APIs, Interactive Dashboard, End-to-End Verification.
