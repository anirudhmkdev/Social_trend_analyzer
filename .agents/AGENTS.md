# Specialist repository guidance

Start with root `AGENTS.md` for durable constraints. Read `PRD.md`, `ARCHITECTURE.md`, `DATA_SCHEMA.md` and `NLP_PIPELINE.md` for current implementation contracts; `docs/CODEX_AUDIT.md` records executed verification. The roadmap is historical, not an acceptance report.

Backend routes stay thin; orchestration lives in services, inference/preprocessing in NLP modules, scoring in `nlp/trends/`. All results and joins are run-scoped. Preserve canonical original/cleaned/sentiment representations, UTC timestamps, preprocessing version reuse and NULL-versus-zero engagement. Keep centered neutral momentum and recency modulation; do not replace the documented formula with simple multiplication or sentiment weights.

No production behavior should change because pytest is running. Inference fixtures belong only in tests, with a separate real-model smoke. Never silently fall back to random embeddings, heuristic sentiment/entity naming or arbitrary fixed topic counts. Expose small-corpus methods and NER degradation in recorded metadata.

Frontend contracts mirror Pydantic envelopes. Native forms/dialogs and React resource hooks are sufficient; no SWR, shadcn, Recharts or Axios are currently used. Read the Impeccable skill when changing UI, preserve the Ledger design, and verify meaningful desktop/mobile states after relevant edits.

Dependencies originate in pyproject/package.json, with generated locks. Run the documented checks and distinguish fixture integration, learned-model smoke, fresh installation and unavailable PostgreSQL verification. Do not commit local datasets, staging, caches or verification output.
