---
name: Social Trend Analyzer
description: High-precision NLP trend intelligence and computational linguistics workbench
colors:
  primary: "#0f172a"
  primary-foreground: "#f8fafc"
  accent: "#0284c7"
  accent-hover: "#0369a1"
  accent-subtle: "#e0f2fe"
  neutral-bg: "#f8fafc"
  neutral-surface: "#ffffff"
  neutral-subtle: "#f1f5f9"
  border: "#e2e8f0"
  border-subtle: "#f1f5f9"
  border-strong: "#cbd5e1"
  text-primary: "#0f172a"
  text-secondary: "#334155"
  text-muted: "#64748b"
  sentiment-pos: "#059669"
  sentiment-pos-bg: "#ecfdf5"
  sentiment-pos-border: "#a7f3d0"
  sentiment-neu: "#475569"
  sentiment-neu-bg: "#f1f5f9"
  sentiment-neu-border: "#cbd5e1"
  sentiment-neg: "#e11d48"
  sentiment-neg-bg: "#fff1f2"
  sentiment-neg-border: "#fecdd3"
  trend-emerging: "#d97706"
  trend-emerging-bg: "#fffbeb"
  trend-emerging-border: "#fde68a"
  trend-rising: "#0d9488"
  trend-rising-bg: "#f0fdfa"
  trend-rising-border: "#99f6e4"
  trend-stable: "#475569"
  trend-stable-bg: "#f8fafc"
  trend-stable-border: "#e2e8f0"
  trend-declining: "#64748b"
  trend-declining-bg: "#f3f4f6"
  trend-declining-border: "#e5e7eb"
typography:
  display:
    fontFamily: "Space Grotesk, system-ui, sans-serif"
    fontSize: "clamp(1.5rem, 3vw, 2rem)"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "-0.03em"
  headline:
    fontFamily: "Space Grotesk, system-ui, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "-0.02em"
  title:
    fontFamily: "IBM Plex Sans, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: "-0.01em"
  body:
    fontFamily: "IBM Plex Sans, system-ui, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "0em"
  label:
    fontFamily: "JetBrains Mono, monospace"
    fontSize: "0.6875rem"
    fontWeight: 500
    lineHeight: 1.3
    letterSpacing: "0.03em"
rounded:
  none: "0px"
  sm: "2px"
  md: "4px"
  lg: "6px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "24px"
  xxl: "32px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.primary-foreground}"
    rounded: "{rounded.sm}"
    padding: "6px 14px"
  button-secondary:
    backgroundColor: "{colors.neutral-surface}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.sm}"
    padding: "6px 14px"
  badge-trend:
    rounded: "{rounded.sm}"
    padding: "2px 6px"
  kpi-tile:
    backgroundColor: "{colors.neutral-surface}"
    rounded: "{rounded.md}"
    padding: "16px"
---

# Design System: Social Trend Analyzer

## Overview

**Creative North Star: "The Precision Intelligence Ledger"**

Social Trend Analyzer is conceived as a serious, scientific computational instrument—the digital analog to a high-density financial terminal or an empirical laboratory observatory. It completely rejects the superficial tropes of modern consumer "AI SaaS" products (floating glass cards, neon gradient blurs, oversized marketing hero banners, and generic rounded containers). Instead, the system prioritizes uncompromising data legibility, mathematical explainability, and structured information hierarchy.

The aesthetic philosophy centers on **quiet technical authority**: the application frame recedes into an architectural, monochromatic slate grid, allowing high-resolution statistical metrics, topic distributions, sentiment spectra, and temporal plots to command the viewer's attention. Every UI element carries purpose; decoration is excised in favor of structural clarity, high text-to-canvas contrast, and dense tabular scanability.

**Key Characteristics:**
- **Architectural & Monochromatic:** Grounded in cool slate neutrals with crisp 1px structural borders rather than diffuse drop shadows.
- **Data-Led Color Semantics:** High-saturation color is strictly rationed; it functions exclusively to convey verified data states (positive/negative sentiment, emerging/rising velocity, pipeline health).
- **Engineered Typographical Pairing:** Geometric, technical headlines paired with a balanced, highly legible UI body and a dedicated tabular monospace font for all numbers, tokens, formulas, and timestamps.
- **Workbench Layouts:** Compact, modular grids and edge-to-edge inspector panels tailored for analytical workflows rather than marketing pitches.
- **Verifiable Integrity:** Flat, unembellished components that communicate academic rigor and computational transparency.

---

## Colors

The palette is intentionally restrained. The visual environment is anchored by monochromatic slate and deep ink tones, reserving distinct chromatic accents exclusively for semantic signals.

### Primary & Interface
- **Primary Ink** (`#0f172a`): Used for primary action buttons, dominant titles, active navigation states, and strong typography.
- **Deep Steel Focus** (`#0284c7`): Technical cyan-blue reserved strictly for keyboard focus rings, active tab indicators, and interactive filter states (occupies ≤5% of screen real estate).
- **Steel Accent Subtle** (`#e0f2fe`): Low-opacity background tint for active filters or selected row highlights.

### Neutrals (Structure & Canvas)
- **Canvas Base** (`#f8fafc`): Crisp, slightly cool off-white background providing high contrast without the harsh glare of pure `#ffffff`.
- **Surface Elevation** (`#ffffff`): Clean white container surfaces for data tables, KPI blocks, and inspector panels.
- **Subtle Surface** (`#f1f5f9`): Header backgrounds, table row alternate striping, and inactive toolbars.
- **Border Structural** (`#e2e8f0`): 1px boundary lines defining panels, table headers, and status cards.
- **Border Subtle** (`#f1f5f9`): Internal sub-dividers separating sub-metrics.
- **Text Primary** (`#0f172a`): High-contrast ink for values, table headers, and primary content.
- **Text Secondary** (`#334155`): Secondary descriptive text and column values.
- **Text Muted** (`#64748b`): Metadata labels, parameter descriptions, and timestamps.

### Semantic: Sentiment Distributions
- **Positive** (`#059669` / bg: `#ecfdf5` / border: `#a7f3d0`): Subdued emerald green for positive sentiment ratios and positive growth deltas.
- **Neutral** (`#475569` / bg: `#f1f5f9` / border: `#cbd5e1`): Balanced slate for neutral sentiment and stable volume.
- **Negative** (`#e11d48` / bg: `#fff1f2` / border: `#fecdd3`): Muted crimson rose for negative sentiment spikes and anomalous churn.

### Semantic: Trend Dynamics
- **Emerging Trend** (`#d97706` / bg: `#fffbeb` / border: `#fde68a`): Amber-gold signaling a nascent topic with high burstiness or rapid early acceleration.
- **Rising Trend** (`#0d9488` / bg: `#f0fdfa` / border: `#99f6e4`): Deep teal indicating sustained multi-window momentum and growth.
- **Stable Trend** (`#475569` / bg: `#f8fafc` / border: `#e2e8f0`): Architectural slate for baseline activity ($0.50$ normalized trend score).
- **Declining Trend** (`#64748b` / bg: `#f3f4f6` / border: `#e5e7eb`): Soft cool gray indicating negative velocity or receding attention.

### Named Rules
- **The Monochrome Foundation Rule:** 90% of any view must consist of canvas, surface, border, and grayscale typography. Colored pixels are solely semantic data carriers.
- **The Dual-Channel Identification Rule:** Never rely on color alone to communicate state. Every sentiment bar or trend badge must display an accompanying text label or numerical score alongside its tint.
- **The Anti-Gradient Doctrine:** Linear or radial color gradients are strictly forbidden across UI backdrops, buttons, cards, and headers.

---

## Typography

The typography system avoids overused generic sans-serif faces in favor of an engineered analytical hierarchy that balances modern geometric precision with tabular computational rigor.

**Display Font:** `Space Grotesk` (fallback: `system-ui, sans-serif`)  
**Body & UI Font:** `IBM Plex Sans` (fallback: `system-ui, sans-serif`)  
**Tabular & Code Font:** `JetBrains Mono` (fallback: `Menlo, Consolas, monospace`)

**Character:** Technical, deliberate, and academic. Headlines feel drafted with drafting-pen precision, body copy is optimized for sustained analytical reading, and numbers align in crisp fixed-width columns.

### Hierarchy
- **Display** (`weight: 600`, `size: clamp(1.5rem, 3vw, 2rem)`, `line-height: 1.2`, `letter-spacing: -0.03em`): Top-level dashboard headers and primary analytical view titles.
- **Headline** (`weight: 600`, `size: 1.125rem`, `line-height: 1.3`, `letter-spacing: -0.02em`): Section headings, modal titles, and primary panel headers.
- **Title** (`weight: 600`, `size: 0.875rem`, `line-height: 1.4`, `letter-spacing: -0.01em`): Card titles, column header groups, and topic names.
- **Body** (`weight: 400`, `size: 0.8125rem`, `line-height: 1.5`, `letter-spacing: 0em`): Post content preview, descriptions, explanations, and long-form narrative.
- **Label / Quantitative Mono** (`weight: 500`, `size: 0.6875rem`, `line-height: 1.3`, `letter-spacing: 0.03em`): All scores, percentages, z-scores, timestamps, counts, status tags, and model metadata. Always rendered in `JetBrains Mono`.

### Named Rules
- **The Tabular Numerical Rule:** All numeric scores, sample counts, coordinates, timestamps, and p-values must render with font feature settings `tnum` (tabular numbers) and monospaced formatting to ensure vertical alignment in tables and cards.
- **The Compact Scale Doctrine:** Header sizes remain compact (`≤2rem`). Large consumer landing-page display typography has no place in an analytical workbench.

---

## Layout

The spatial model is an organized, high-density analytical workbench adhering to an **8px base grid** with a **4px micro-grid** for internal component padding.

- **Workbench Grid:** Clean 12-column responsive layout with standardized gutters (`16px` on tablet, `20px`–`24px` on desktop).
- **Edge-to-Edge Dividers:** Sections are partitioned by crisp `1px border-slate-200` lines rather than large empty gutters or heavy cards.
- **Master-Detail Flow:** Primary views split into a high-density tabular/chart list on the left (60–70% width) and a sticky contextual inspector panel on the right (30–40% width) for deep post drill-down, topic word-weights, and mathematical parameter breakdowns.
- **Data Table Layout:** Fixed header with virtualized or paginated rows, strict row height (`36px` compact or `44px` standard), explicit column boundaries, and right-aligned numerical data.
- **Zero Card Nesting:** Containers do not nest inside other containers. If a panel contains multiple sections, divide them with horizontal lines or subtle background shifts (`#f8fafc` vs. `#ffffff`), never secondary enclosed boxes with rounded corners.

---

## Elevation & Depth

The system is **flat-by-default with structural border definition**. Depth is communicated through subtle surface tonal contrast and 1px borders rather than diffuse drop shadows.

- **Flat Architecture:** Surfaces rest on the `#f8fafc` canvas with `#ffffff` fills and `1px solid #e2e8f0` borders.
- **Zero Shadows at Rest:** Standard panels, KPI tiles, and tables use `box-shadow: none`.
- **Interactive State Elevation:** On hover or active focus, interactive rows and cards gain a subtle 1px border shift (`border-slate-300` or `border-sky-500`) and a micro-elevation:
  - `shadow-xs`: `0 1px 2px 0 rgba(15, 23, 42, 0.04)` (reserved strictly for elevated popovers or hover states).
- **Prohibited Effects:**
  - No `backdrop-filter: blur(...)` or frosted glass effects.
  - No colored neon glowing borders.
  - No deep atmospheric drop shadows (`rgba(0,0,0,0.15)+`).

---

## Shapes

The form language is disciplined, rectilinear, and architectural:

- **Radius Scale:**
  - `none` (`0px`): Table cells, full-width dividers, split-pane panels, tab headers.
  - `sm` (`2px`): Badges, status tags, monospaced code snippets, button micro-controls.
  - `md` (`4px`): Standard buttons, input fields, dropdown menus, KPI metric containers.
  - `lg` (`6px`): Root dashboard container borders, modal windows.
- **Absolute Bans:**
  - Radii greater than `6px` are prohibited.
  - Fully rounded pill shapes (`rounded-full` on buttons, filters, or large cards) are strictly banned.
  - Asymmetric or organic shapes are prohibited.

---

## Components

### Buttons
- **Shape:** Micro-radius (`rounded: 2px` or `4px`).
- **Primary:** Background `#0f172a`, text `#f8fafc`, padding `6px 14px`, font size `0.8125rem`, font weight `500`. Hover shifts to `#334155`.
- **Secondary / Outlined:** Background `#ffffff`, border `1px solid #e2e8f0`, text `#0f172a`, padding `6px 14px`. Hover shifts to `#f8fafc` with `border-slate-300`.
- **Destructive:** Background `#ffffff`, border `1px solid #fecdd3`, text `#e11d48`. Hover shifts to `#fff1f2`.

### KPI Metric Tiles
- **Structure:** Clean white rectangular container with `1px solid #e2e8f0` border and `padding: 16px`.
- **Header:** Uppercase monospaced label in `JetBrains Mono` (`size: 0.6875rem`, color `#64748b`, letter spacing `0.04em`).
- **Value:** High-contrast display in `Space Grotesk` or tabular mono (`size: 1.5rem`–`1.75rem`, color `#0f172a`, font weight `600`).
- **Context Footer:** Micro-badge indicating percentage shift or baseline comparison ($z$-score or standard deviation) with explicit sign (`+` or `-`).

### Data Tables
- **Header:** Compact height (`32px`), background `#f8fafc`, uppercase monospaced labels (`0.6875rem`), bottom border `1px solid #e2e8f0`.
- **Row:** Height `36px` to `40px`, border bottom `1px solid #f1f5f9`. Hover state shifts background to `#f8fafc`.
- **Numeric Alignment:** All quantitative columns (post counts, trend scores, burstiness z-scores, sentiment fractions) strictly right-aligned with fixed monospaced type.
- **Text Alignment:** Topic labels, keywords, and entity names left-aligned.

### Trend Status Badges
- **Shape:** Micro-radius (`2px`), padding `2px 6px`, font `JetBrains Mono` (`0.6875rem`, weight `500`).
- **Variants:**
  - *Emerging:* Text `#d97706`, bg `#fffbeb`, border `1px solid #fde68a`.
  - *Rising:* Text `#0d9488`, bg `#f0fdfa`, border `1px solid #99f6e4`.
  - *Stable:* Text `#475569`, bg `#f8fafc`, border `1px solid #e2e8f0`.
  - *Declining:* Text `#64748b`, bg `#f3f4f6`, border `1px solid #e5e7eb`.

### Sentiment Distribution Bar
- **Structure:** Continuous segmented horizontal bar with zero gaps or rounded joins.
- **Segments:** Positive (`#059669`), Neutral (`#64748b`), Negative (`#e11d48`).
- **Accompanying Legend:** Crisp tabular percentage breakdown displayed directly underneath.

### Filter & Time-Window Toolbar
- **Style:** Compact segmented control group with square/2px-rounded joined borders.
- **Active State:** Solid fill (`#0f172a`) with white text (`#f8fafc`).
- **Inactive State:** Background `#ffffff`, text `#475569`, border `1px solid #e2e8f0`.

---

## Do's and Don'ts

### Do:
- **Do** format all numerical data, scores, dates, and mathematical formulas in `JetBrains Mono` with tabular figures (`tnum`).
- **Do** use 1px solid structural borders (`#e2e8f0`) to establish clear visual boundaries between functional workbench modules.
- **Do** preserve high text contrast (minimum 4.5:1 ratio against backgrounds) across all labels, table rows, and status badges.
- **Do** provide explicit mathematical explanations alongside trend scores (e.g. showing growth baseline, acceleration, burstiness z-score, and recency attenuation).
- **Do** keep layouts compact and information-dense, allowing researchers to evaluate dozens of topics, entities, and sentiment signals simultaneously.
- **Do** pair every color indicator with an unambiguous text label or quantitative figure.

### Don't:
- **Don't** use purple, blue, or violet AI gradients across backgrounds, hero cards, or borders.
- **Don't** use glassmorphism, background blurs (`backdrop-blur`), or glossy specular highlights.
- **Don't** use pill-shaped (`rounded-full`) buttons, filter tags, or status badges.
- **Don't** use card borders with radius greater than 6px, and never nest cards inside other cards.
- **Don't** rely on generic "Inter-everywhere" typography; maintain the distinct pairing of `Space Grotesk`, `IBM Plex Sans`, and `JetBrains Mono`.
- **Don't** insert arbitrary decorative icons or meaningless emoji into cards and headers.
- **Don't** use continuous pulsing, bouncing, or spinning animations; transitions must be rapid (`≤150ms`) and functional only.
- **Don't** fabricate, mock, or simulate analytical scores or sparklines; all visuals must reflect real calculations.
