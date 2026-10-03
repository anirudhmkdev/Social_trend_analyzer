# Codex implementation audit

Baseline: `f26e072`, inspected 2026-10-03. Original checkout was clean on `phase-1-foundation`; no hardening branch existed. Work continues on `codex/hardening`. This is a code-backed audit, not acceptance of the previous phase claims.

## Findings before fixes

| ID / severity | Affected files | Observed behavior and root cause | User impact | Correction / disposition |
|---|---|---|---|---|
| A01 CRITICAL | `backend/app/services/dataset_service.py`, `api/v1/datasets.py` | Upload saves an untracked randomly named file. Preview and validation read posts before any posts are imported. `import_dataset` requires bytes again and has no HTTP route. | A user cannot finish custom CSV ingestion; validation can claim zero rows are valid. | Fix: tracked UUID staging, raw preview/detection, actual source validation, explicit import route and immutable lifecycle. |
| A02 HIGH | `backend/app/services/dashboard_service.py:search_posts` | Sentiment and PostTopic joins omit run IDs. | Two runs multiply rows and mix labels, breaking pagination and search. | Fix: required dataset/run context, scoped joins, stable pagination, date filters, two-run regression. |
| A03 HIGH | `frontend/src/lib/api.ts`, dataset/topic pages | Datasets expects an array instead of `{datasets,total}`; topic list, topic detail text, engagement and trend-history contracts also disagree. | Runtime crash, missing post text, ineffective classifications. | Fix parallel Pydantic/TS contracts and real response tests; no unsafe casting. |
| A04 CRITICAL | `nlp/topics/embedder.py`, `nlp/enrichment/ner.py`, `nlp/topics/modeler.py` | Missing embeddings produce hash-seeded random vectors; NER heuristically labels generic capitalized words PRODUCT; broad BERTopic catch silently uses KMeans. Metadata claims the configured models regardless. PYTEST environment changes production code behavior. | Apparently successful analyses can be unrelated to their texts and misleading to evaluators. | Remove silent substitutes/test switches; fail core model stages clearly; omit NER with explicit degraded metadata; name the legitimate small-corpus method. |
| A05 HIGH | `backend/pyproject.toml`, `requirements.lock` | Production imports pandas, numpy, emoji, transformers, torch, sentence-transformers, sklearn, spaCy, BERTopic, UMAP, HDBSCAN, multipart absent from source metadata. | A clone cannot reproduce the application from its declared dependencies. | Fix complete production imports, lean dev group, generated lock and fresh install. |
| A06 HIGH | `services/dataset_service.py`, `database/engine.py`, `models/dataset.py` | Deletion has no staged-file cleanup or active-run guard. SQLite engine does not enable foreign keys; Dataset has no run cascade relationship. | Orphan results/files and deletion during inference. | Fix SQLite FK enforcement, ORM cascades and conflict guard; verify SQLite/PostgreSQL migrations. |
| A07 HIGH | `services/dashboard_service.py`, topic/trend/enrichment endpoints | Missing run selects latest completed globally; invalid run may be treated as no data. No shareable dataset/run context in UI. | A user can view the wrong dataset or mistake a failed request for an empty result. | Fix explicit selection and validated context, URL parameters, all lifecycle states. |
| A08 HIGH | `api/v1/endpoints/topics.py:get_topic_detail` | Calculates whole-topic sentiment and engagement on `.limit(50)`; sample is arbitrary first ten. | Biased statistics presented as topic totals. | Fix full scoped aggregates, representative ordering, entity/keyword/hashtag and history evidence. |
| A09 HIGH | `nlp/trends/aggregator.py`, `engine.py` | Only occupied windows are compared; a topic's last occupied window becomes its latest snapshot even when it disappeared before dataset end. | False growth across gaps and stale current volumes. | Fix complete UTC window series through the dataset reference time and zero-volume windows; document recency/reference clock. |
| A10 MEDIUM | `ingestion/sample_generator.py`, README, frontend | Generator claims ~850 rows without a test for actual count; pattern totals not scaled to specification. | Demo content/size claims cannot be trusted. | Fix deterministic ~850–1000 rows while preserving five themes, platforms, temporal patterns; assert size and trends. |
| A11 MEDIUM | `nlp/topics/modeler.py` | Default five-post clusters; labels concatenate three terms without redundant token/stem cleanup; representatives are first records. | Repetitive micro-topic names and weak evidence. | Evaluate real demo outputs; improve cluster sizing and conservative display naming while retaining raw keywords/index. |
| A12 HIGH | frontend `/datasets`, `/dashboard`, `/topics`, `/search` | Demo-only actions, no upload/mapping/details/history, topics assume nonexistent classification fields, client filtering, errors only logged. | Primary product workflow and recovery are incomplete. | Fix dataset management, scoped server filtering, progress and visible recovery states. |
| A13 MEDIUM | frontend `/`, Sidebar, Header, dashboard | Phase-1 status page, Overview, LIVE, static Pipeline Online, alpha/version and continuous monitoring copy. | Misrepresents batch processing and exposes obsolete development content. | Remove Overview/status artifacts; root redirects; rename Explorer and Analysis; retain true health and methodology. |
| A14 MEDIUM | dashboard, globals.css, layout components | Timeline is equal-height day tiles; tiny labels, no responsive sidebar, missing semantic filter labels/focus/chart alternative. | Difficult temporal comparisons and keyboard/mobile usage. | Preserve Ledger identity; real accessible time series, ranked table first, consistent forms and focus, native deletion dialog. |
| A15 HIGH | `backend/tests`, frontend package | Backend switches model behavior under pytest; frontend has no automated test scripts or E2E. | Passing tests don't establish production contracts or real inference. | Explicit injected fixtures; contract/lifecycle/isolation regressions; real-server UI E2E plus separate full NLP smoke. |
| A16 MEDIUM | README, PRD, ARCHITECTURE, DATA_SCHEMA, NLP_PIPELINE, MODEL_EVALUATION, PROJECT_REPORT_NOTES | Claims phase completion, 80 tests/87%, Recharts, wrong formula (sentiment instead of velocity), unsupported throughput/benchmark numbers and migration plan. MIT file absent. | Reproducibility and academic claims exceed evidence. | Correct current docs, preserve academic requirements/history with clear labels, add MIT license and executed evidence only. |
| A17 MEDIUM | `services/analysis_service.py`, preprocessing pipeline | Empty dataset marked completed; mapping presence instead of non-null mapping determines engagement availability; failure does not rollback before persisting failed state; preprocessing overwrites mapped hashtags. | Misleading completion, incorrect weights, stuck run after DB error and lost source tags. | Fix input readiness, engagement values, rollback/recovery and preserve mapped tags. |

## Additional defects verified during implementation

| ID / severity | Files / evidence | Root cause and impact | Final disposition |
|---|---|---|---|
| A18 HIGH | Historical `analysis_runs.model_info`; `005_legacy_provenance.py`, `AnalysisContext.tsx` | Old completed analyses could retain apparently authoritative model names despite the previously silent substitutes. Changing new-run behavior cannot verify old results. | Resolved: preserve records and mark incomplete historical provenance `legacy_unverified`; show rerun guidance. Upgrade regression seeds both old and verified completed runs. |
| A19 HIGH | Real-model smoke; `services/analysis_service.py` | NumPy integer cluster IDs were bound as binary values instead of native integers, making persisted topic joins unreliable despite unit fixture success. | Resolved: cast model IDs before persistence; real 90/900-post inference and scoped investigation executed. |
| A20 MEDIUM | Alembic metadata check; `models/post.py`, `models/analysis_run.py` | ORM-created duplicate indexes did not match the committed named migration indexes. Metadata-created test tables masked the drift. | Resolved: retain the existing migration indexes; actual migration upgrade/check/downgrade/re-upgrade passes. |
| A21 HIGH | Browser integration regression; `AnalysisContext.tsx` | Context URL canonicalization could overwrite navigation immediately after an upload and return the user to the list. | Resolved: dataset routes own their route context; E2E verifies navigation to the uploaded source and subsequent analysis. |
| A22 LOW | `frontend/src/lib/utils.ts`, package metadata, external font build | Unused class-composition helpers/packages and build-time remote font requests added unnecessary dependencies and failure points. | Removed unused utilities, `clsx`, `tailwind-merge`, unused `pytest-asyncio`; bundle the existing three font families locally. |

## Final report

### 1. Critical/high defects found

The pre-edit audit confirmed two critical findings (A01 incomplete ingestion; A04 fabricated/silently substituted inference) and ten high findings (A02/A03/A05/A06/A07/A08/A09/A12/A15/A17). A18/A19/A21 were additionally verified during implementation. Severity describes user impact, not a formal vulnerability scan.

### 2. Resolved defects

A01–A17 are resolved in the implemented scope; A18–A21 are also resolved. PostgreSQL runtime verification is explicitly deferred, rather than included in the claim for A06.

- Upload one CSV, retain its tracked local artifact, preview original strings, detect/correct mappings, validate actual source rows, inspect issues and import only valid rows transactionally. Status transitions are explicit; mapping edits reset validation; repeated import is idempotent. Preserve original post text and leading-zero external IDs. Reject ambiguous duplicate/empty CSV headers and unsupported binary input.
- Optional invalid engagement becomes unavailable; genuine zero remains measurable. Duplicate text is retained and flagged. Reject zero-valid imports/empty analyses. Preserve source hashtags alongside extracted hashtags.
- Dataset deletion cascades posts, analyses and derived rows, cleans staging and blocks active runs. SQLite foreign keys are enabled. Legacy staging failures have a recovery message. Existing older demo data is preserved with explicit replacement instructions.
- Require and validate run/dataset context for derived data; scope every sentiment/topic/entity/keyword/trend join. Search uses literal keyword matching, stable pagination and inclusive UTC date filters. Topic totals use the full assignment set; representative posts are separately bounded.
- Fill calendar gaps through the dataset reference timestamp; apply one shared TrendEngine to persisted and filtered/windowed evidence. Show the minimum-three-post guard independently of the numeric score.
- Fail missing core models clearly; optional NER completes in disclosed degraded mode. Record actual methods/parameters/packages instead of the configured-model fiction. Roll back failures before persisting failed status. Restart marks interrupted jobs failed, releasing the single-process active-run guard.

### 3. Removed

Removed the Phase-1 root Overview, roadmap/framework/migration cards, LIVE and continuous-monitoring language, hard-coded Pipeline Online, alpha/development sidebar content, duplicate navigation and silent random/hash/KMeans/heuristic-NER substitutes. Removed unused class utilities/packages and pytest-asyncio. Replaced stale benchmark, completion and unsupported accuracy/throughput claims with measured evidence. Academic documents remain useful and current; Git retains the original planning history.

### 4. Retained

Retained the existing FastAPI/SQLAlchemy/Next.js implementation and Precision Intelligence Ledger design. Datasets remains the primary ingestion path; the deterministic demo remains a secondary reproducible onboarding path. Dashboard answers what changed; Trends & Topics and Explorer investigate the evidence; Analysis retains academic model/method/formula transparency. Historical roadmap is labeled as planning. No remote LLM, streaming connector, authentication system or additional queue/service was introduced.

### 5. Backend files changed

Exact paths added/modified relative to `f26e072`:

```text
backend/alembic.ini
backend/app/api/v1/datasets.py
backend/app/api/v1/endpoints/analysis.py
backend/app/api/v1/endpoints/dashboard.py
backend/app/api/v1/endpoints/enrichment.py
backend/app/api/v1/endpoints/topics.py
backend/app/api/v1/endpoints/trends.py
backend/app/database/engine.py
backend/app/database/migrations/versions/003_staged_uploads.py
backend/app/database/migrations/versions/004_topic_provenance.py
backend/app/database/migrations/versions/005_legacy_provenance.py
backend/app/ingestion/csv_parser.py
backend/app/ingestion/normalizer.py
backend/app/ingestion/sample_generator.py
backend/app/ingestion/validator.py
backend/app/main.py
backend/app/models/analysis_run.py
backend/app/models/dataset.py
backend/app/models/post.py
backend/app/models/topic.py
backend/app/nlp/enrichment/ner.py
backend/app/nlp/preprocessing/pipeline.py
backend/app/nlp/sentiment/classifier.py
backend/app/nlp/topics/embedder.py
backend/app/nlp/topics/modeler.py
backend/app/nlp/trends/aggregator.py
backend/app/nlp/trends/engine.py
backend/app/schemas/dashboard.py
backend/app/schemas/dataset.py
backend/app/schemas/topic.py
backend/app/schemas/trend.py
backend/app/services/analysis_service.py
backend/app/services/context.py
backend/app/services/dashboard_service.py
backend/app/services/dataset_service.py
backend/app/services/topic_service.py
backend/app/services/trend_service.py
backend/pyproject.toml
backend/requirements.lock
backend/scripts/full_nlp_smoke.py
backend/tests/__init__.py
backend/tests/conftest.py
backend/tests/e2e_server.py
backend/tests/model_fixtures.py
backend/tests/test_api/test_analytics.py
backend/tests/test_hardening.py
backend/tests/test_migrations.py
backend/tests/test_nlp/test_enrichment.py
backend/tests/test_nlp/test_sentiment.py
backend/tests/test_nlp/test_topics.py
backend/tests/test_nlp/test_trends.py
backend/tests/test_recovery.py
```

### 6. Frontend files changed

Exact paths added/modified/removed relative to `f26e072` (utils.ts removed):

```text
frontend/eslint.config.mjs
frontend/next.config.ts
frontend/package-lock.json
frontend/package.json
frontend/playwright.config.ts
frontend/src/app/analysis/page.tsx
frontend/src/app/dashboard/page.tsx
frontend/src/app/datasets/[id]/page.tsx
frontend/src/app/datasets/page.tsx
frontend/src/app/explorer/page.tsx
frontend/src/app/globals.css
frontend/src/app/layout.tsx
frontend/src/app/page.tsx
frontend/src/app/pipeline/page.tsx
frontend/src/app/search/page.tsx
frontend/src/app/topics/[id]/page.tsx
frontend/src/app/topics/page.tsx
frontend/src/components/ActivityChart.tsx
frontend/src/components/AnalysisContext.tsx
frontend/src/components/DeleteDataset.tsx
frontend/src/components/Feedback.tsx
frontend/src/components/TrendTable.tsx
frontend/src/components/layout/AppShell.tsx
frontend/src/components/layout/Header.tsx
frontend/src/components/layout/Sidebar.tsx
frontend/src/hooks/useResource.ts
frontend/src/lib/api.ts
frontend/src/lib/utils.ts
frontend/tests/api.test.ts
frontend/tests/e2e/product.spec.ts
frontend/tsconfig.json
```

### 7. Migrations added

- `003_staged_uploads`: nullable tracked staging filename and upload metadata; existing records preserved.
- `004_topic_provenance`: nullable JSON raw model topic identity/keyword provenance.
- `005_legacy_provenance`: marks old completed runs without current NER/topic provenance as unverified, preserving their original metadata/results.

Existing migrations 001/002 were preserved. The regression upgrades from 002 with existing seeded data, verifies preservation/provenance and metadata drift, downgrades to base and re-upgrades. Production verification SQLite also upgraded through 005. PostgreSQL runtime has not been tested because the Docker daemon is unavailable.

### 8. Dependency changes

`pyproject.toml` declares every production data/NLP import plus actual dev tools. `requirements.lock` is generated from it with hashes and the official CPU PyTorch index. Tested packages include torch 2.14.1+cpu, transformers 5.18.0, sentence-transformers 6.1.0, spaCy 3.8.16, BERTopic 0.17.4, NumPy 2.5.3 and pandas 3.0.6; exact resolved dependencies belong in the lock. The optional official spaCy English model 3.8.0 is documented separately and was installed for real verification. Neither caches nor binaries are committed.

Frontend retains Next 15.5.26 / React 19.1.0, adds local Fontsource families and proportionate Playwright/tsx tests, removes unused composition packages. `npm ci` uses the updated committed lock. No chart library was added: a small native SVG has focus/hover readouts and an exact data table.

### 9. NLP quality changes and measured output

Core inference uses actual local CardiffNLP RoBERTa, MiniLM embeddings, BERTopic/UMAP/HDBSCAN/c-TF-IDF, plus optional spaCy. There are no production pytest switches. Small corpora (<15 posts) disclose their agglomerative method. Cluster minimum scales with corpus size; conservative complete-link centroid similarity merges near duplicates without a target count. Labels deduplicate terms/stems and use local readable families; raw topic IDs/keywords remain visible.

NER omits hashtag tokens and obvious generic/accidental predictions, preserves supported entity types and records availability/version. A missing model returns no fabricated entities and a clear degraded warning. Existing unverified runs are visibly marked.

Real HTTP smoke (existing model caches; CPU, no inference fixtures):

| Corpus | Valid posts | Non-outlier topics | Outlier posts | Sentiment + / neutral / − | Workflow seconds |
|---|---:|---:|---:|---|---:|
| Uploaded source | 90 | 4 | 0 | 21 / 52 / 17 | 44.94 |
| Bundled demo | 900 | 25 | 53 (5.89%) | 176 / 582 / 142 | 27.20 |

The original stored run used 1,535 posts, 136 non-outlier topics and 26 outliers. These counts compare different generator sizes; they are not a controlled coherence/accuracy benchmark. The new demo has 21 UTC days, three platforms and tested source-pattern intent for rising AI, declining crypto, stable sports/climate and emerging health. Learned latest topic classifications are not forced to match generator themes (demo latest: one Emerging, 24 Stable; small topics are guarded).

Inspected actual names, keyword provenance, representatives, entities, sentiment, outliers and classifications in `NLP_SMOKE_EVIDENCE.json`. Current names include Public Health Crisis and AI/Crypto/Sports families with descriptors. Some repetitive/subtopic labels and spaCy errors remain (NFT/Paris Agreement ORG). No sentiment accuracy, NER precision/recall or external-data coherence benchmark is claimed.

### 10. UI/UX changes

Five clear product destinations; root and legacy-route redirects. CSV upload is primary; demo secondary. Explicit dataset/run selectors and shareable URL context, actual status/progress/history, loading/error/empty/not-analyzed/pending/running/failed/completed states, recovery actions and confirmed deletion.

Ranked trend table leads the dashboard: label/classification/score/volume/growth/sentiment/trajectory/reason. Full explanations expand, and guarded classifications state the insufficient current volume. A real temporal chart shows total activity and sentiment composition with keyboard/hover detail plus an exact table. Topic detail provides complete aggregates, history and raw provenance. Explorer filters on the server. Analysis shows actual model statuses, package versions and the correct recency-centered formula.

Preserved Space Grotesk, IBM Plex Sans, JetBrains Mono, light canvas, structural borders, small radii and restrained semantic colors. Native forms, labels, table headers, skip link, visible focus, progress, dialog and chart alternatives improve accessibility. Desktop and 390px mobile visuals were inspected; mobile navigation/tables scroll and selectors stack. This is bounded keyboard/mobile QA, not a formal WCAG conformance audit.

### 11. Test results

| Executed check | Final result |
|---|---|
| Ruff (`app tests scripts`) | Passed |
| mypy (`app`) | Passed, 73 source files |
| pytest in fresh Python 3.12.13 environment | **91 passed**, 69.74s, three dependency warnings |
| Alembic SQLite preservation/drift/downgrade/re-upgrade | Passed in regression and verification DB |
| ESLint (src/tests/config) | Passed |
| TypeScript noEmit | Passed |
| Frontend API tests | **4 passed** |
| Next production build | Passed, all 12 generated routes |
| Fixture integration E2E | **1 passed**, 30.4s suite / 12.4s workflow; opt-in real demo test correctly skipped |
| Real-model upload-to-Analysis browser flow | **1 passed**, 6.6s suite / 5.2s workflow (warmed models) |
| Real-model demo action/new-run/dashboard browser flow | **1 passed**, 51.6s workflow |
| Real-model HTTP upload + demo smoke | Both passed |
| Fresh locked backend install and uv pip check | Passed, 101 locked packages; 102 with optional spaCy model |
| Clean frontend npm ci | Passed, 335 packages |
| Impeccable mechanical frontend audit | Zero findings in the bounded scan |
| git diff --check | Passed |
| PostgreSQL/Docker runtime | Deferred; daemon pipe unavailable |

Warnings are Starlette's httpx test-client deprecation and seeded UMAP's single-job notices. None are failing checks. Integration fixtures are injected only by tests; production routes/persistence are exercised. Earlier selector/CORS-origin test setup failures were corrected and the affected workflows rerun. A Windows preview file lock was resolved before the clean npm reinstall. Temporary approval/build timeout was retried successfully; no approval blocker remains.

### 12. Coverage

Backend statement coverage: **92.559% (2,861 / 3,091 statements; 230 missing)**, conventionally displayed as 93%. Branch coverage was not enabled. Frontend has four API tests and browser workflow assertions, not an instrumented coverage percentage. Fixtures establish contracts/orchestration rather than model accuracy; the separate real-model tests cover that integration boundary.

### 13. Fresh-install result

Created a separate empty `.venv-verify` using Python 3.12.13, installed the generated hashed dependency lock and ran compatibility checks, static checks, tests, migrations and real inference from that environment. Installed the optional official spaCy model explicitly. Stopped the frontend preview, performed clean npm ci from the updated lock, then built and started the production frontend. This establishes the documented Windows/SQLite install path, without depending on undeclared developer-venv packages. Linux/macOS and PostgreSQL installs were not independently executed. Core model weights used existing local caches; first-use model download requires network access and is not a clean-cache download benchmark.

### 14. Full E2E result

The **actual production UI and API with real model weights** completed: upload a five-row CSV once → raw preview → manual text/date mapping → validate (four valid, one invalid, two duplicates retained) → confirm/import → trigger analysis → await new completed run → correctly scoped Dashboard → Trends & Topics → topic detail/history/representatives → Explorer keyword search (three OpenAI posts in the selected run) → Analysis → desktop/mobile dashboard. No HTTP responses or production model inference were mocked in this mode.

The **Use Demo Dataset UI action** also loaded the 900-post source, triggered a new real analysis, awaited a newly completed run and opened its scoped dashboard (run `755928b6-73d0-4b51-9042-c3c56570eda2`). Separately, the repeatable default E2E starts isolated real FastAPI routes/migrations/DB and Next.js while injecting only inference fixtures. The HTTP full NLP smoke verifies the larger uploaded corpus and demo, including actual topics, search and methodology metadata. Evidence boundaries remain explicit.

Local screenshots and full raw responses are under ignored `.verification`; compact synthetic evidence is committed. Existing developer database was not replaced or modified by verification.

### 15. Deferred / retained limitations

- PostgreSQL runtime migration/cascade/install verification remains deferred because Docker's Linux-engine pipe is unavailable; SQLite is the executed path. This is not a claim that PostgreSQL testing passed.
- One in-process worker / one server process; restart fails interrupted work for explicit retry. No durable queue or multi-process locking. Large datasets can consume substantial CPU/RAM; smoke is 90/900 posts, not a 50MB stress benchmark.
- English short-text models, 128-token sentiment truncation, synthetic-template bias and imperfect names/entities. No external ground-truth quality benchmark.
- Installed libraries did not expose the exact sentiment/embedding cache revision; metadata records null honestly. Package versions/parameters/NER version are recorded, but model downloads are not guaranteed immutable by model name alone.
- Local single-user operation has no authentication. Raw CSV/text remains on this machine until deletion; deleting a dataset does not remove external copies/backups/model caches. File and database deletion cannot share one atomic transaction; a rare database commit failure after unlink would require restaging. Upload/import are transactionally guarded within the database.
- Validation issue display is capped at 200; date ambiguity assumes the documented parser order, so ISO timestamps are preferable. Older uploads with missing stage files require explicit re-upload. Older demo data requires explicit delete/reload; no user data was silently regenerated.
- Browser verification used installed Chrome; mobile QA is viewport-based, not physical-device testing. No frontend coverage percentage, formal accessibility certification, clean model-cache download test or PostgreSQL result is claimed.

### 16. Git commits created

Logical commits on `codex/hardening`, without history rewrite, push or merge:

```text
5ed3c24 docs: record implementation audit and repository constraints
d54a401 build: declare and lock the CPU NLP dependencies
95e1673 fix: complete upload-once dataset staging and import lifecycle
bb0967c fix: isolate derived results and complete temporal evidence
f7e9a5b fix: disclose model provenance and improve topic and entity quality
523df3e feat: deliver the scoped Ledger ingestion and investigation workbench
487b839 test: cover lifecycle isolation recovery and real browser workflows
```

This final audit, updated current documentation, evidence and MIT license are recorded in the following documentation commit (`docs: record verified hardening results and limitations`). Its hash is available from `git log -1` and the final handoff; the report cannot contain its own commit hash without another commit.

Other documentation/repository files changed:

```text
.agents/AGENTS.md
.gitignore
AGENTS.md
ARCHITECTURE.md
DATA_SCHEMA.md
IMPLEMENTATION_ROADMAP.md
LICENSE
NLP_PIPELINE.md
PRD.md
PRODUCT.md
README.md
docs/CODEX_AUDIT.md
docs/MODEL_EVALUATION.md
docs/NLP_SMOKE_EVIDENCE.json
docs/PROJECT_REPORT_NOTES.md
```

### 17. Git status

Handoff state: clean tracked working tree on `codex/hardening` after the documentation commit. The final `git status --porcelain` and `git diff --check` checks are performed after committing and confirmed in the handoff. No push/merge occurred. Local virtual environments, model caches, databases, uploads, verification screenshots/raw responses and test build output remain ignored. The project knowledge graph was refreshed for the current implementation (2,552 nodes / 6,477 edges; no repository artifact written).
