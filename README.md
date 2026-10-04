# Social Trend Analyzer

A local, CPU-based workbench for investigating trends in English social-media CSV datasets. Upload once, review the original rows, map fields, validate, import valid posts and run NLP. Every derived view belongs to an explicit dataset and analysis run.

## Quick start (Windows PowerShell)

Requirements: Python 3.12, Node.js 20 or newer, and [uv](https://docs.astral.sh/uv/). SQLite is the default. PostgreSQL is optional; set `DATABASE_URL` before running migrations. Use one backend server process.

```powershell
git clone https://github.com/anirudhmkdev/Social_trend_analyzer.git
cd Social_trend_analyzer/backend
uv venv .venv --python 3.12
uv pip sync --python .venv/Scripts/python.exe requirements.lock --index-strategy unsafe-best-match
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m alembic upgrade head
# Optional entity enrichment; omit to run with explicitly reported NER degradation:
uv pip install --python .venv/Scripts/python.exe --no-deps https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In another terminal:

```powershell
cd Social_trend_analyzer/frontend
npm ci
Copy-Item .env.local.example .env.local
npm run dev
```

Open [the workbench](http://localhost:3000), then Datasets → Add Dataset. The first analysis downloads CardiffNLP RoBERTa and MiniLM weights from Hugging Face into the local model cache. Network access is needed for this initial download; subsequent inference is local. Core model loading failure marks the analysis failed with a recovery message; no random vectors or heuristic sentiment substitute is used. Missing spaCy weights omit entities and mark the completed run as degraded. Install the optional model and restart before analyzing again. Do not commit caches, databases or uploaded files.

Linux/macOS: use `.venv/bin/python` in place of `.venv/Scripts/python.exe`. The tested environment is Windows/Python 3.12; portability has not been independently exercised here. The lock includes the official CPU PyTorch index and hashes. `pyproject.toml` is the dependency source.

## CSV workflow

UTF-8 (including BOM) or Windows-1252 CSV, maximum 50 MB. Text and timestamp are required. Platform, hashtags, author/external ID and likes/comments/shares are optional. Common column aliases are suggested; confirm and correct the mapping before validation. Naive timestamps assume UTC. Ambiguous day/month dates follow the documented parser order (US month/day before day/month); ISO timestamps are preferable.

Uploaded → Mapped → Validated → Imported → Preprocessed. Mapping edits reset validation. Validation examines the staged source; row details show the first 200 issues with zero-based indices excluding the header. Missing/short text and missing/invalid timestamps exclude rows. Repeated text remains imported and is flagged as duplicate, because recurrence over time can matter. Optional invalid engagement becomes unavailable (`NULL`), whereas a measured zero stays zero. Import with no valid rows is rejected. A repeated import returns the existing dataset without duplicating posts. Imported datasets are immutable; upload a corrected file as a new dataset.

Staged filenames are server-generated UUIDs. Files remain local until dataset deletion, which also cascades posts, runs and derived results. Active analyses block deletion. The batch worker is an in-process background task, not a durable queue; server restart marks interrupted jobs failed and allows retry. Run exactly one server process, without reload during analysis.

## Investigation

| Page | Purpose |
|---|---|
| Dashboard | Selected dataset/run, platform and UTC hourly/daily/weekly window; ranked trends first, real time series and evidence |
| Datasets | Upload, raw preview, detection, mapping, validation, import, analysis progress/history and confirmed deletion |
| Trends & Topics | Server-filtered labels, keywords and latest classifications; outlier count |
| Topic detail | Full topic aggregates, trend/sentiment history, representative posts, entities, keywords, hashtags and raw model provenance |
| Explorer | Original text search with platform, sentiment, topic, inclusive UTC date filters and stable pagination |
| Analysis | Methodology, actual model status, package versions, fixed parameters, formula and recorded run statistics |

`/` redirects to `/dashboard`; legacy `/search` and `/pipeline` URLs redirect to Explorer and Analysis. URL parameters `dataset`, `run`, `window`, `platform` are shareable context. Invalid/deleted context is shown as an error with recovery; APIs do not select the latest run globally. Selecting a dataset without a run chooses its latest completed run in the UI and records that choice in the URL.

## Models and interpretation

- [CardiffNLP Twitter-RoBERTa sentiment](https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment-latest): CC-BY-4.0, English, three classes; input truncates to 128 tokens.
- [MiniLM embeddings](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2): Apache-2.0, 384 dimensions.
- BERTopic + seeded UMAP + HDBSCAN + c-TF-IDF; no target topic count. Minimum cluster size scales with dataset size. Very similar centroids merge conservatively; raw IDs/keywords remain available. Below 15 posts, an explicitly recorded agglomerative method is used. Labels are local keyword-derived summaries, not ground truth.
- [spaCy en_core_web_sm](https://spacy.io/models/en#en_core_web_sm): optional MIT model. NER preserves case, excludes hashtag tokens and filters obvious generic/accidental entities. Predictions can still be wrong.

The 900-post deterministic demo covers five themes, three platforms and 21 UTC days: rising AI, declining crypto, stable sports/climate and emerging health. Generator intent is tested; it is not an accuracy benchmark for learned topic assignments.

Existing demo records from the older generator are preserved. The demo action explains how to delete/reload them explicitly. Migration 005 marks historical completed runs without current provenance as unverified; rerun to obtain current model metadata.

Let `M = .35 volume + .25 engagement + .20 velocity + .20 burst`, with centered logistic signals. `TrendScore = .5 + (M − .5) × recency`. Missing engagement redistributes its weight. Recency references the dataset's latest timestamp. Classification thresholds: Emerging ≥ .70 with new/reappearing activity, Rising ≥ .60, Stable ≥ .40, otherwise Declining. **Current volume < 3 forces Stable**, even with a high score. The UI explains this guard. Sentiment does not affect TrendScore; Burst is a signal, not a separate class. See [NLP methodology](NLP_PIPELINE.md).

## Verification

```powershell
cd backend
.\.venv\Scripts\python.exe -m ruff check app tests scripts
.\.venv\Scripts\python.exe -m mypy app
.\.venv\Scripts\python.exe -m pytest --cov=app --cov-report=term-missing
# Real weights and a running API on port 8000, using a separate disposable database:
.\.venv\Scripts\python.exe scripts/full_nlp_smoke.py
cd ../frontend
npm run lint
npx tsc --noEmit
npm test
npm run build
# Install Chrome or change the Playwright channel to installed Chromium.
# On Linux/macOS set E2E_PYTHON to an absolute .venv/bin/python path.
npm run test:e2e
# Optional: real weights, migrated disposable DB, backend 8000 and production UI 3000 running:
$env:E2E_REAL_NLP='1'
npm run test:e2e
Remove-Item Env:E2E_REAL_NLP
```

Unit/integration tests inject inference fixtures only from `backend/tests/model_fixtures.py`. The E2E starts the real FastAPI routes, migrations and database on port 8001 plus Next.js on 3001; it substitutes inference, not HTTP responses. It has its own `.next-e2e` output and `.verification/e2e.db`. The full-model smoke exercises a 90-row custom upload and the 900-post demo with real RoBERTa, MiniLM, BERTopic and spaCy. Do not confuse those evidence boundaries. [Audit, measured results and limitations](docs/CODEX_AUDIT.md) is the verification record.

PostgreSQL 16.14 runtime verification passed on 2026-10-04: all five migrations, schema drift check, rollback/re-upgrade on an empty temporary database, two real-model 90-post runs, scoped investigation, production browser upload workflow and cascade/artifact deletion. Verification used the repository Compose service on an alternate local port because another PostgreSQL listener occupied 5432. Existing user databases were preserved. See the audit follow-up for connection details, counts and evidence boundaries; this does not establish populated production-data rollbacks or model accuracy.

Regenerate the backend lock after changing `pyproject.toml`:

```powershell
uv pip compile pyproject.toml --extra dev --python-version 3.12 --generate-hashes --emit-index-url --extra-index-url https://download.pytorch.org/whl/cpu --index-strategy unsafe-best-match -o requirements.lock
```

## Documentation and license

[Requirements](PRD.md) · [Product context](PRODUCT.md) · [Design](DESIGN.md) · [Architecture](ARCHITECTURE.md) · [Schema](DATA_SCHEMA.md) · [NLP](NLP_PIPELINE.md) · [Evaluation](docs/MODEL_EVALUATION.md) · [Academic report notes](docs/PROJECT_REPORT_NOTES.md). The roadmap is historical planning and does not establish completion. Project code is MIT licensed; pretrained model/data licenses remain separate. See [LICENSE](LICENSE).
