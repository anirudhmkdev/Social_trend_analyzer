# Social Trend Analyzer requirements and implementation scope

The product answers “What changed, and why?” for a user-supplied English social-media dataset. This is a local, CPU-only academic project with batch analysis and inspectable evidence.

## Acceptance workflow

Upload one CSV → preview raw rows/detection → correct and confirm mappings → validate actual source → inspect invalid/duplicate details → confirm import of valid rows → trigger analysis → inspect progress/history → dashboard for that exact dataset/run → topic evidence → server-filtered Explorer → methodology and model status.

The secondary demo contains exactly 900 deterministic posts, five themes, three platforms and 21 UTC days. It preserves rising AI, declining crypto, stable sports/climate and emerging health generator intent. Discovered clusters are learned results and need not coincide one-to-one with these themes.

## Supported scope

- CSV only, UTF-8/BOM or Windows-1252, ≤50 MB; required text and timestamp. Other normalized fields are optional. Source-column suggestions do not replace explicit mapping review.
- Safe local staging, actual pre-import validation, transactional/idempotent import, immutable imported sources and versioned preprocessing reuse, confirmed deletion with cascade/artifact cleanup.
- One active local background run; terminal success/failure and startup interruption recovery. NER can complete in explicitly degraded mode. Core model absence fails visibly.
- Canonical dataset/run selection in shareable URLs. Metrics, assignments and joins never merge unrelated datasets or runs. Native loading, empty, failed, missing/deleted-context and retry states.
- Hourly/daily/weekly buckets and platform views recompute the scoring logic. Rank trends centrally; classify Emerging/Rising/Stable/Declining, with an explained three-post guard. Burst is a signal, not a fifth class.
- Whole-topic sentiment/engagement/history/entity/keyword aggregates and separately labeled representative samples. Raw model cluster IDs/terms remain inspectable.
- Explorer keyword, platform, sentiment, topic and inclusive UTC date range filters, server pagination and stable ordering.
- Accessible tables/forms/focus/dialogs; compact Ledger typography, one-pixel borders, restrained semantic color; real time-series chart with focus/hover detail and exact data alternative.
- Dependency declarations and generated locks, unit/API/regression/migration coverage, fixture-injected real-server browser integration and distinct real-model smoke evidence.

## Deliberate exclusions and limits

No live social-media ingestion, JSON import, authentication, multi-tenancy, remote LLMs, queues, microservices, vector database or claimed real-time monitoring. No accuracy/throughput claim without executed appropriately labeled evidence. No internet-facing deployment guarantee. PostgreSQL is supported by dialect-aware models/migrations, but runtime verification depends on a working server; see audit limitations.

Earlier aspirations such as separate Burst classification, phase-status pages, Recharts/SWR or continuous monitoring are not implemented product requirements. Historical development sequencing remains in `IMPLEMENTATION_ROADMAP.md`; current verification is in `docs/CODEX_AUDIT.md`.
