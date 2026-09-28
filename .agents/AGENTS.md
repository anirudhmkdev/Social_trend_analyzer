# AGENTS.md — Development & Verification Instructions

> **Project:** Social Trend Analyzer  
> **Updated:** 2026-08-09  

---

## Project Overview

Social Trend Analyzer is a full-stack NLP application that ingests social-media post datasets and automatically discovers emerging topics, trending keywords/hashtags, sentiment, named entities, and temporal trends. It surfaces insights through an interactive analytics dashboard.

**Repository structure:** Monorepo with `backend/` (Python/FastAPI) and `frontend/` (Next.js/TypeScript).

---

## Development Rules

### General

1. **Read before writing.** Always read existing files before modifying them. Understand the context.
2. **Do not rewrite working code unnecessarily.** Make targeted changes.
3. **Never fabricate data, metrics, or results.** All numbers displayed to the user must come from actual computations.
4. **Do not commit secrets.** Use `.env` files (gitignored). Provide `.env.example`.
5. **Prefer simple, maintainable solutions.** This is a college project — it must be understandable.
6. **Keep concerns separated:**
   - NLP code lives in `backend/app/nlp/` only.
   - Trend scoring lives in `backend/app/nlp/trends/` only.
   - API routes are thin controllers — they call services.
   - Frontend consumes REST APIs — no business logic in React components.
7. **Add tests for important algorithms.** Especially: preprocessing, sentiment, topic modeling, trend scoring.
8. **Add docstrings/comments for mathematically important logic.** Trend scoring formula, normalization, signal computation.
9. **Validate all API inputs** using Pydantic schemas.
10. **Handle errors explicitly.** Use custom exceptions. Return appropriate HTTP status codes.
11. **Preserve reproducibility.** Pin dependencies. Use random seeds. Store model versions.
12. **Do not add unnecessary dependencies.** Every package must have a clear purpose.
13. **Do not prematurely optimize.** Get it working correctly first.
14. **Do not silently change project requirements.** If something seems wrong, flag it.
15. **Verify work before marking tasks complete.** Run tests. Check the UI. Confirm the API response.

### Backend-Specific

- **Python version:** 3.11–3.12
- **Framework:** FastAPI with Pydantic v2
- **ORM:** SQLAlchemy 2.x with explicit dialect-aware JSON (`PortableJSON = JSON().with_variant(JSONB(), "postgresql")`)
- **Linting:** Ruff (replaces flake8, isort, black)
- **Type checking:** mypy (with `--ignore-missing-imports` for NLP libraries)
- **Testing:** pytest + httpx (for TestClient)
- **Database:** PostgreSQL (primary), SQLite (dev fallback)
- **Migrations:** Alembic
- **Dependency Management:** Single source of truth in `pyproject.toml` compiled into committed `requirements.lock` via `pip-compile` / `uv pip compile`. Do not maintain drifting manual lists.
- **Background Tasks & Concurrency:** FastAPI `BackgroundTasks` is used as a lightweight, single-machine demo architecture for college evaluation (not a durable production job queue). Concurrency is strictly limited to **1 active analysis run at a time** (returns HTTP 409 Conflict if an analysis is already running).
- **Run Lifecycle:** `AnalysisRun` records `created_at` on enqueue, `started_at` is nullable while pending (set when worker starts), `completed_at` is nullable until completion/failure.
- **Timestamps:** All imported post timestamps and temporal aggregations are strictly normalized to **UTC**.
- **NLP models:** Load lazily on first use. Cache in memory. CPU-only.

### Frontend-Specific

- **Framework:** Next.js 15 with App Router (use a supported, security-patched release; pin via committed `package-lock.json`)
- **Language:** TypeScript (strict mode)
- **Styling:** Tailwind CSS (v4)
- **Components:** shadcn/ui
- **Charts:** Recharts
- **Linting:** ESLint + Prettier
- **State management:** React hooks + SWR or React Query for data fetching
- **API client:** Fetch or Axios with typed wrappers

### NLP-Specific

- **Preprocessing Policy:** Preprocessing is dataset-scoped, canonical and immutable for `preprocessing_version="1.0.0"`. It executes once for a dataset when the preprocessing stage is run (Phase 3), before NLP analysis. Subsequent `AnalysisRuns` reuse the canonical preprocessed representations rather than overwriting them. Preprocessing configuration is fixed/versioned rather than configurable independently for each AnalysisRun, preserving reproducibility without coupling Phase 2 to Phase 3.
- **Text Representations:**
  - `original_text`: Raw unmodified text; never discard or mutate.
  - `cleaned_text`: Lowercased, URLs removed, mentions normalized/removed, hashtag `#` stripped. For topic modeling, TF-IDF, c-TF-IDF, and search.
  - `sentiment_ready_text`: Case-preserved with `@user` and `http` tokens. For sentiment classification.
  - *NER Text:* Case-preserved clean text derived deterministically at runtime from `original_text`. Never pass lowercased text to spaCy NER.
- **Embeddings:** `all-MiniLM-L6-v2` (Sentence Transformers, batch size 64)
- **Sentiment:** `cardiffnlp/twitter-roberta-base-sentiment-latest` (License: CC-BY-4.0, ~124M tweets training, 3 labels: negative, neutral, positive)
- **NER:** `en_core_web_sm` (spaCy) operating on runtime case-preserved text
- **Topics:** BERTopic initialized with `nr_topics=None` (preserving HDBSCAN micro-clusters; no premature topic reduction) and UMAP `random_state=42`
- **Trend Detection:**
  - Zero growth is mathematically neutral ($M_{\text{base}} = 0.50$, $\text{TrendScore} = 0.50 \implies \text{Stable}$) using centered logistic normalization ($S(x) = \frac{1}{1 + e^{-kx}}$ where $0 \to 0.50$).
  - Recency is a relevance/modulation factor ($R \in (0, 1]$), NOT an additive growth signal: $\text{TrendScore} = 0.5 + (M_{\text{base}} - 0.5) \times R$.
  - Burstiness z-score is strictly described in standard deviations above/below baseline.
  - **Missing Engagement vs Genuine Zero Engagement:** Numeric zero engagement (`likes=0, comments=0, shares=0`) is a valid measurement ($e_g = 0 \implies S(0) = 0.50$). Redistribute engagement weight ($w_{\text{eng}} \to 0$) ONLY when engagement metrics are unavailable/unmapped in the dataset source (detected via dataset column mapping / metadata). Do not fabricate missing values.
- **Local Execution:** All models run locally on CPU. No remote API calls for inference.
- **Batch processing:** Always batch transformer and embedding calls; never send one text at a time.

---

## File Conventions

### Backend

```
backend/app/api/v1/          # Route handlers (thin controllers)
backend/app/services/         # Business logic orchestration
backend/app/nlp/              # NLP pipeline modules
backend/app/models/           # SQLAlchemy ORM models
backend/app/schemas/          # Pydantic request/response schemas
backend/app/ingestion/        # Data import and validation
backend/app/database/         # DB engine, sessions, migrations
backend/app/core/             # Cross-cutting (exceptions, logging)
backend/tests/                # All tests mirror app/ structure
```

### Frontend

```
frontend/src/app/             # Next.js pages (App Router)
frontend/src/components/      # React components
frontend/src/components/ui/   # shadcn/ui base components
frontend/src/lib/             # API client, types, utilities
frontend/src/hooks/           # Custom React hooks
```

### Naming

- **Python:** snake_case for files, functions, variables. PascalCase for classes.
- **TypeScript:** PascalCase for components and types. camelCase for functions and variables.
- **Files:** Descriptive names. One module/component per file.

---

## Verification Checklist

Run these checks before considering any phase complete:

### Backend

```bash
cd backend

# Linting
python -m ruff check app/ tests/

# Type checking
python -m mypy app/ --ignore-missing-imports

# Tests
pytest tests/ -v

# Server starts
uvicorn app.main:app --port 8000
```

### Frontend

```bash
cd frontend

# Linting
npm run lint

# Type checking
npx tsc --noEmit

# Build
npm run build

# Dev server starts
npm run dev
```

### Database

```bash
cd backend

# Migrations
alembic upgrade head

# Downgrade (test rollback)
alembic downgrade -1
alembic upgrade head
```

### Full Pipeline Smoke Test

After Phase 7+:

```bash
# 1. Start PostgreSQL (via Docker Compose)
docker compose up -d db

# 2. Run migrations
cd backend && alembic upgrade head

# 3. Start backend
uvicorn app.main:app --port 8000 &

# 4. Load sample data
curl -X POST http://localhost:8000/api/v1/datasets/sample

# 5. Trigger analysis
curl -X POST http://localhost:8000/api/v1/analysis/run -H "Content-Type: application/json" -d '{"dataset_id": "<id>"}'

# 6. Poll status
curl http://localhost:8000/api/v1/analysis/<run_id>/status

# 7. Check dashboard data
curl http://localhost:8000/api/v1/dashboard/summary

# 8. Start frontend
cd frontend && npm run dev

# 9. Open browser: http://localhost:3000/dashboard
```

---

## Environment Variables

### Backend (`backend/.env`)

```bash
# Database
DATABASE_URL=postgresql://dev:dev@localhost:5432/social_trend_analyzer
# Fallback: sqlite:///./social_trend_analyzer.db

# API
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000

# NLP (optional overrides)
EMBEDDING_MODEL=all-MiniLM-L6-v2
SENTIMENT_MODEL=cardiffnlp/twitter-roberta-base-sentiment-latest
SPACY_MODEL=en_core_web_sm

# Reproducibility
RANDOM_SEED=42

# Upload
MAX_UPLOAD_SIZE_MB=50
UPLOAD_DIR=./uploads
```

### Frontend (`frontend/.env.local`)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| PyTorch too large | Install CPU-only: `pip install torch --index-url https://download.pytorch.org/whl/cpu` |
| spaCy model not found | Run: `python -m spacy download en_core_web_sm` |
| Alembic migration conflicts | Check `versions/` directory; resolve manually if autogenerate creates conflicts |
| CORS errors in browser | Verify `CORS_ORIGINS` in backend config matches frontend URL |
| BERTopic needs min cluster size | For small datasets (<100 posts), lower `min_cluster_size` to 5 |
| Out of memory on large datasets | Reduce batch sizes for embeddings and sentiment inference |
| SQLite JSON limitations | Use `PortableJSON = JSON().with_variant(JSONB(), "postgresql")` in models; avoid PostgreSQL-specific JSONB operators in raw queries |

---

## Key Reference Documents

| Document | Path | Purpose |
|----------|------|---------|
| PRD | `PRD.md` | Product requirements |
| Architecture | `ARCHITECTURE.md` | System design |
| NLP Pipeline | `NLP_PIPELINE.md` | NLP module details |
| Data Schema | `DATA_SCHEMA.md` | Database design |
| Roadmap | `IMPLEMENTATION_ROADMAP.md` | Phase-by-phase plan |
| Model Eval | `docs/MODEL_EVALUATION.md` | Evaluation metrics (Phase 11+) |
| Report Notes | `docs/PROJECT_REPORT_NOTES.md` | Academic report support (Phase 12) |
