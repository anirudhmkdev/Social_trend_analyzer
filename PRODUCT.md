# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

- **College Evaluators & Academic Examiners (Primary):** Faculty, advisors, and external examiners evaluating NLP pipeline rigor, algorithmic correctness, model selection validity, statistical explanations, and full-stack software architecture.
- **Student Demonstrators & Researchers (Secondary):** Project owners and student researchers presenting live demonstrations using bundled sample datasets or custom CSV/JSON post collections to showcase real-time topic discovery, sentiment trends, and burst detection.
- **Data Analysts & Social Researchers (Tertiary):** Analysts exploring text dynamics across volume, sentiment distributions, named entities, and temporal shifts without needing cloud subscriptions or commercial APIs.

## Product Purpose

Social Trend Analyzer is a self-contained, research-grade natural language processing application that ingests social-media post datasets to automatically discover latent topics, rank trending themes, quantify sentiment dynamics, extract named entities, and expose temporal trajectories. It solves the barrier of cost and opacity inherent in commercial enterprise listening tools (e.g., Brandwatch, Meltwater) by delivering a fully local, reproducible, and mathematically explainable analytics workbench executable on standard consumer CPU hardware.

Success means:
1. Ingesting, validating, and normalizing arbitrary social post datasets (CSV/JSON) with UTC timestamp standardization.
2. Generating canonical, immutable text preprocessing artifacts (`preprocessing_version="1.0.0"`) once per dataset.
3. Performing unsupervised topic modeling (BERTopic with HDBSCAN micro-clusters) and transformer sentiment inference (CardiffNLP RoBERTa) entirely on CPU.
4. Computing mathematically grounded trend scores where zero growth is strictly neutral ($0.50$) and burstiness is quantified in standard deviations.
5. Surfacing all results in a high-density, professional analytics dashboard that favors data clarity, tabular inspection, and statistical evidence over marketing spectacle.

## Positioning

Unlike enterprise "black-box" SaaS dashboards or superficial AI wrappers that rely on paid third-party APIs and generative hallucination:
- **Local & Offline Execution:** All NLP inference runs locally on CPU with pinned dependencies and random seed $42$.
- **Mathematical Transparency:** Trends are computed via explicit statistical formulations (centered logistic normalization, recency modulation, and burstiness z-scores), accompanied by inspectable metric breakdowns.
- **Canonical Preprocessing Immutability:** Preprocessed representations (`original_text`, `cleaned_text`, `sentiment_ready_text`, and runtime case-preserved NER text) are canonical and reproducible across analysis runs.
- **Academic Rigor:** Dedicated pipeline transparency views display model provenance, token counts, processing latency, and evaluation metrics.

## Operating Context

- **Environment:** Academic evaluation labs, seminar presentations, and local research workstations.
- **Hardware Profile:** Standard multi-core consumer CPU, 8GB–16GB RAM, local SSD storage; zero GPU or cloud API dependency.
- **Workflows:**
  1. *Dataset Ingestion & Validation:* Upload CSV/JSON, auto-map columns, review data health (missing values, invalid dates, duplicates), normalize timestamps to UTC.
  2. *Pipeline Execution:* Trigger single-run asynchronous NLP background task; track execution phases via status endpoints.
  3. *Analytical Exploration:* Inspect global KPIs, filter topics by trend velocity, explore sentiment distributions, drill down into topic detail pages with representative posts, and cross-reference extracted entities.
  4. *Audit & Verification:* Inspect processing metadata, model parameters, and statistical formulas on the Architecture & Analysis page.

## Capabilities and Constraints

- **Confirmed Capabilities:**
  - Automated CSV & JSON ingestion with interactive column mapping and schema validation.
  - Canonical dataset text preprocessing: lowercased cleaned text for topics/TF-IDF, case-preserved tokenized text for CardiffNLP RoBERTa, and runtime case-preserved text for spaCy NER.
  - Sentiment classification into Positive, Neutral, Negative with softmax confidence distributions.
  - Dynamic BERTopic modeling preserving HDBSCAN micro-clusters (`nr_topics=None`, UMAP `random_state=42`).
  - c-TF-IDF keyword extraction and spaCy `en_core_web_sm` entity recognition.
  - Multi-factor trend detection: centered logistic growth $S(x)$, recency attenuation $R \in (0, 1]$, burstiness z-scores, and numeric vs. missing engagement weighting.
  - High-density analytics dashboard built with Next.js 15, TypeScript strict mode, Tailwind CSS v4, and Recharts.
- **Technical Constraints:**
  - Strict single-concurrency for active analysis runs (FastAPI returns HTTP 409 Conflict if another run is in progress).
  - All post timestamps and temporal aggregations strictly normalized to UTC.
  - CPU-only execution; all transformers run with batching (batch size 64 for embeddings, batch size 32 for RoBERTa).
  - Zero fabricated or synthetic data in dashboard outputs: every KPI, curve, and badge reflects real database computations.

## Brand Commitments

- **Name:** Social Trend Analyzer (abbreviated **STA**).
- **Tone & Identity:** Serious modern analytics and research instrument. Methodical, authoritative, understated, clinical, and data-dense.
- **Visual Boundaries (Strictly Binding):**
  - No purple or blue "AI" neon gradients.
  - No glassmorphism, backdrop blurs, or glowing border halos.
  - No oversized consumer-SaaS hero banners or marketing fluff.
  - No excessive rounded cards, bubbly buttons, or pill-shaped chips.
  - No generic Inter-everywhere typography.
  - No arbitrary decorative icons used as fillers.
  - No continuous bouncing or distracting looping animations.
  - No nested cards inside cards; enforce clean single-level borders and flat tonal separation.

## Evidence on Hand

- **Repository Artifacts:**
  - Product Requirements Document (`PRD.md`)
  - Architectural Specification (`ARCHITECTURE.md`)
  - NLP Pipeline Blueprint (`NLP_PIPELINE.md`)
  - Relational Schema Design (`DATA_SCHEMA.md`)
  - Phase Implementation Plan (`IMPLEMENTATION_ROADMAP.md`)
- **Codebase Foundations:**
  - `backend/`: FastAPI application, Alembic database migrations (`001_initial`), SQLAlchemy models (`Dataset`, `Post`), comprehensive health and configuration tests.
  - `frontend/`: Next.js 15 App Router shell, Tailwind CSS v4, Lucide icons, responsive navigation frame.
- **Strict Absence Rules:** No external API keys (OpenAI, Twitter API, Anthropic) are permitted for core pipeline execution; ground-truth evaluation metrics are rendered only when ground-truth labels exist.

## Product Principles

1. **Truth in Computation:** Every score, metric, percentage, and sparkline originates from verifiable deterministic or statistical calculations. Never simulate analytics or display placeholder numbers.
2. **Algorithmic Explainability:** Every trend score must be decomposable into its constituent signals (growth baseline, acceleration, burstiness z-score, recency attenuation factor).
3. **Information Density over Decorative Space:** Prioritize tabular clarity, high-contrast typography, and scannable visual structures over gratuitous padding and consumer-grade card layouts.
4. **Autonomous Local Operation:** The product functions completely offline on a single laptop without cloud service requirements.
5. **Architectural Discipline:** Strict separation between NLP execution, thin API controllers, and presentation components.

## Accessibility & Inclusion

- Adherence to WCAG 2.1 AA contrast ratios (minimum 4.5:1 for normal body text, 3:1 for large headers and interface components).
- High-contrast border distinctions (`#e2e8f0` light / `#27272a` dark) to avoid relying on subtle shadow differences alone.
- Multi-dimensional data encoding: charts and status indicators must pair color with shape, numeric text, or textual labels (e.g. sentiment states and trend dynamics always show explicit text alongside color indicators).
- Full keyboard navigability across tabular datasets, search filters, and inspector modals with visible focus rings.
