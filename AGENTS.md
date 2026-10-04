# Repository engineering constraints

- Prefer codebase-memory-mcp graph tools for code discovery; index this repository when needed. Use text search for literals/configuration or insufficient graph results.
- Modify the existing implementation; keep this a local, CPU-only college project. No remote inference, authentication, queues, or additional services.
- Routes call services; NLP belongs in `backend/app/nlp/`, trend mathematics in its `trends/` package. Use validated Pydantic inputs and parallel strict TypeScript contracts.
- Every derived result and join must belong to one analysis run and its dataset. Preserve original text, normalize timestamps to UTC, and reuse versioned dataset preprocessing.
- Never fabricate metrics or silently substitute models. Record degradation, actual model details, and verification limitations.
- Upload once, persist staging safely, validate that source, import atomically, and clean artifacts on deletion. Imported datasets are immutable; analyze them repeatedly instead of reimporting.
- Keep one active background analysis on one local server process. PostgreSQL and SQLite must both support migrations and deletion cascades.
- `backend/pyproject.toml` is the dependency source; generate `requirements.lock`. Use `npm ci` with committed `package-lock.json`. Exclude model caches, local databases, uploaded data, and verification artifacts from Git.
- Preserve the Precision Intelligence Ledger typography, restrained colors, compact tables, accessible forms, visible focus, and honest batch-analysis language.
- Run Ruff, mypy, pytest/coverage, migrations, ESLint, TypeScript, build, frontend tests, and critical E2E after relevant changes. Keep fixture integration evidence distinct from full-model smoke evidence.
- Use logical commits; do not rewrite history, push, or merge without instructions.

References: [product requirements](PRD.md), [product context](PRODUCT.md), [design](DESIGN.md), [architecture](ARCHITECTURE.md), [schema](DATA_SCHEMA.md), [NLP](NLP_PIPELINE.md), [audit and verification](docs/CODEX_AUDIT.md), [specialist agent guidance](.agents/AGENTS.md). The roadmap is historical planning, not implementation evidence.
