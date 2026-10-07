# Social Trend Analyzer

A local, CPU-based workbench for investigating trends in English social-media CSV datasets. Upload once, review the original rows, map fields, validate, import valid posts and run NLP. Every derived view belongs to an explicit dataset and analysis run.

## Quick start (Windows PowerShell)

Requirements: Python 3.12, Node.js 20 or newer (with npm), and [uv](https://docs.astral.sh/uv/). SQLite is the default, so Docker and PostgreSQL are not required for this setup. PostgreSQL is optional; set `DATABASE_URL` in `backend/.env` before running migrations. Use one backend server process.

The commands below use the existing checkout at `C:\Users\Anirudh\Desktop\Projects\NLP`. If your project is elsewhere, replace that path with your repository folder. To obtain a new checkout instead:

```powershell
git clone https://github.com/anirudhmkdev/Social_trend_analyzer.git
```

### First-time setup: backend (terminal 1)

Open PowerShell and run:

```powershell
Set-Location 'C:\Users\Anirudh\Desktop\Projects\NLP\backend'
uv venv .venv --python 3.12
uv pip sync --python .venv/Scripts/python.exe requirements.lock --index-strategy unsafe-best-match
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
# Required: update the database schema before starting the backend.
.\.venv\Scripts\python.exe -m alembic upgrade head
# Optional entity enrichment; omit to run with explicitly reported NER degradation:
uv pip install --python .venv/Scripts/python.exe --no-deps https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Leave this terminal running. The environment-copy command preserves an existing `.env`; check its `DATABASE_URL` if you previously configured PostgreSQL. For SQLite, the example value is `sqlite:///./social_trend_analyzer.db`. Run migrations and the API from the `backend` folder so the database and upload paths resolve consistently. Virtual-environment activation is not needed because the commands use its Python executable directly.

### First-time setup: frontend (terminal 2)

Open a second PowerShell terminal and run:

```powershell
Set-Location 'C:\Users\Anirudh\Desktop\Projects\NLP\frontend'
npm ci
if (-not (Test-Path .env.local)) { Copy-Item .env.local.example .env.local }
npm run dev
```

Leave this terminal running too. `frontend/.env.local` should contain `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1` for the backend command above. Restart the frontend after changing this value.

| Local page | URL |
|---|---|
| Workbench | [http://localhost:3000](http://localhost:3000) |
| Interactive API documentation | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) |
| API health | [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health) |

Open the workbench, then **Datasets → Add Dataset**. Upload a CSV, review the preview, confirm the field mapping, validate, import valid rows, then start analysis. Wait for the run to finish before inspecting its Dashboard, Trends & Topics or Explorer results. The [download links below](#download-external-test-datasets-kaggle) provide suitable external inputs.

The first analysis downloads CardiffNLP RoBERTa and MiniLM weights from Hugging Face into the local model cache. Network access is needed for this initial download; subsequent inference is local. Core model loading failure marks the analysis failed with a recovery message; no random vectors or heuristic sentiment substitute is used. Missing spaCy weights omit entities and mark the completed run as degraded. Install the optional model and restart before analyzing again. Do not commit caches, databases or uploaded files.

### Run again after setup

For normal use, open two PowerShell terminals. Dependency installation and environment copying are first-time steps. Run the migration command below before starting the backend, including after pulling updates. It brings the database schema up to the version expected by the code; when already current, it makes no changes. Starting Uvicorn alone does not apply migrations.

Terminal 1 — backend:

```powershell
Set-Location 'C:\Users\Anirudh\Desktop\Projects\NLP\backend'
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Terminal 2 — frontend:

```powershell
Set-Location 'C:\Users\Anirudh\Desktop\Projects\NLP\frontend'
npm run dev
```

Visit [http://localhost:3000](http://localhost:3000). Stop each server with **Ctrl+C** when finished. Keep the backend running throughout analysis, with one process and without `--reload`; restarting it interrupts active jobs.

### Common startup problems

| Problem | What to check |
|---|---|
| `uv`, Python or `npm` is not found | Install the prerequisites and reopen PowerShell. The backend lock and verified setup target Python 3.12. |
| Database connection error or missing tables | Check `backend/.env`, start PostgreSQL if selected, and run `.\.venv\Scripts\python.exe -m alembic upgrade head` from `backend`. |
| Header says API available, but dataset requests return HTTP 500 | The health check can succeed with an outdated database schema. Stop the backend, run `.\.venv\Scripts\python.exe -m alembic upgrade head` from `backend`, restart it, then refresh the browser. |
| Frontend cannot reach the API | Keep terminal 1 running and confirm `NEXT_PUBLIC_API_URL` above. Open the health URL to check the API separately. |
| Port 8000 or 3000 is already occupied | Stop the previous project server. If changing ports, update the frontend API URL and backend `CORS_ORIGINS` to match the actual frontend origin. |
| First analysis fails while loading models | Check internet access for the initial weight downloads, read the run's error message, and retry after fixing the reported cause. |

Linux/macOS: use `.venv/bin/python` in place of `.venv/Scripts/python.exe`. The tested environment is Windows/Python 3.12; portability has not been independently exercised here. The lock includes the official CPU PyTorch index and hashes. `pyproject.toml` is the dependency source.

## CSV workflow

UTF-8 (including BOM) or Windows-1252 CSV, maximum 50 MB. Text and timestamp are required. Platform, hashtags, author/external ID and likes/comments/shares are optional. Common column aliases are suggested; confirm and correct the mapping before validation. Naive timestamps assume UTC. Ambiguous day/month dates follow the documented parser order (US month/day before day/month); ISO timestamps are preferable.

Uploaded → Mapped → Validated → Imported → Preprocessed. Mapping edits reset validation. Validation examines the staged source; row details show the first 200 issues with zero-based indices excluding the header. Missing/short text and missing/invalid timestamps exclude rows. Repeated text remains imported and is flagged as duplicate, because recurrence over time can matter. Optional invalid engagement becomes unavailable (`NULL`), whereas a measured zero stays zero. Import with no valid rows is rejected. A repeated import returns the existing dataset without duplicating posts. Imported datasets are immutable; upload a corrected file as a new dataset.

Staged filenames are server-generated UUIDs. Files remain local until dataset deletion, which also cascades posts, runs and derived results. Active analyses block deletion. The batch worker is an in-process background task, not a durable queue; server restart marks interrupted jobs failed and allows retry. Run exactly one server process, without reload during analysis.

## Download external test datasets (Kaggle)

These datasets contain real social-media text and timestamps. Start with the smaller airline file, then use Reddit for a larger external test. Listed CSV sizes fit the current 50 MB upload limit; this does not establish processing speed or successful full-file analysis.

| Dataset and download page | CSV file and listed size | Required field mapping | Useful test |
|---|---|---|---|
| [Twitter US Airline Sentiment — Kaggle](https://www.kaggle.com/datasets/crowdflower/twitter-airline-sentiment) | `Tweets.csv`, approximately 3.42 MB | `text` → Text; `tweet_created` → Timestamp | Sentiment and complaint topics in English airline tweets from February 2015; includes human sentiment labels. |
| [Reddit WallStreetBets Posts — Kaggle](https://www.kaggle.com/datasets/gpreda/reddit-wallstreetsbets-posts) | `reddit_wsb.csv`, approximately 43.73 MB | `title` → Text; `timestamp` → Timestamp | Topics and activity changes around the GameStop period; the publisher's preview spans September 2020–August 2021. |

The airline CSV is also available from this [Hugging Face mirror](https://huggingface.co/datasets/osanseviero/twitter-airline-sentiment/blob/main/Tweets.csv): open the page and click **Download**. Reddit file details are available in the [publisher's input preview](https://www.kaggle.com/code/gpreda/memes-to-markets-wallstreetbets-reddit-nlp/input).

1. Open a Kaggle dataset link and choose **Download**; sign in if prompted.
2. Extract the ZIP and select the CSV named above. Upload the CSV, not the ZIP or any accompanying SQLite database.
3. For an initial CPU test, prepare a sample of about 1,000 rows spread across dates, keeping the header, original text and original timestamps. Sampled counts are only evidence for that sample; use a contiguous time period when evaluating trend curves.
4. In **Datasets → Add Dataset**, upload, map the columns in the table, validate, import and run analysis. Increase the sample only after the smaller run completes.

For airline tweets, `tweet_id` can map to External ID and `name` to Author. Keep `airline_sentiment` separately for an external comparison; the import workflow does not automatically calculate accuracy from ground-truth labels. For Reddit, `id` can map to External ID and `comms_num` to Comments. Use `title` for the first test because many `body` values are missing; combining titles with available bodies requires preparing a text column. Leave Reddit `score` unmapped because net votes are not a count of likes. Preserve genuine timestamps; use ISO dates if converting a different dataset's ambiguous date format.

These are external project test inputs, not proof that the pretrained models never encountered the public posts. Dataset licenses remain separate from this project's MIT license; consult the publisher's terms before redistributing data. Downloaded datasets and any prepared samples should stay outside Git.

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
