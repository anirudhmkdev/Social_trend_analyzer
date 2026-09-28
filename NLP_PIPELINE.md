# Social Trend Analyzer — NLP Pipeline

> **Version:** 1.0  
> **Date:** 2026-08-09  
> **Status:** Draft — Awaiting Review  

---

## 1. Pipeline Overview

```
Raw Social Media Text
        │
        ▼
┌───────────────────────┐
│  1. PREPROCESSING     │   URL removal/replacement, mention normalization,
│                       │   hashtag extraction, emoji handling,
│                       │   whitespace/punctuation cleanup
│                       │   Outputs: original_text (raw),
│                       │   cleaned_text (lowercased),
│                       │   sentiment_ready_text (@user, http),
│                       │   NER representation (case-preserved, runtime)
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│  2. EMBEDDINGS        │   Sentence Transformers
│                       │   Model: all-MiniLM-L6-v2
│                       │   Output: 384-dim dense vectors
└───────────┬───────────┘
            │
            ├──────────────────────────┐
            ▼                          ▼
┌───────────────────────┐  ┌───────────────────────┐
│  3. TOPIC MODELING    │  │  4. SENTIMENT         │
│  UMAP → HDBSCAN      │  │  twitter-roberta-base │
│  → BERTopic/c-TF-IDF │  │  -sentiment-latest    │
│  (nr_topics=None)    │  │  License: CC-BY-4.0   │
│  Input: cleaned_text │  │  Input: sentiment_    │
│  Output: topic_id,    │  │         ready_text    │
│  keywords, names      │  │  Output: label,       │
│                       │  │  confidence scores    │
└───────────┬───────────┘  └───────────┬───────────┘
            │                          │
            ▼                          ▼
┌───────────────────────┐  ┌───────────────────────┐
│  5. KEYWORD/HASHTAG   │  │  6. NAMED ENTITY      │
│  EXTRACTION           │  │  RECOGNITION          │
│  c-TF-IDF, TF-IDF,   │  │  spaCy en_core_web_sm │
│  n-grams, frequency   │  │  Input: case-preserved│
│  Input: cleaned_text  │  │         text (runtime)│
│  Output: ranked       │  │  Output: PERSON, ORG, │
│  keywords & hashtags  │  │  GPE, PRODUCT, EVENT  │
└───────────┬───────────┘  └───────────┬───────────┘
            │                          │
            └──────────┬───────────────┘
                       ▼
            ┌───────────────────────┐
            │  7. TEMPORAL          │
            │  AGGREGATION          │
            │  UTC-normalized time  │
            │  Group by time window │
            │  (hourly/daily/weekly)│
            └───────────┬───────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │  8. TREND DETECTION   │
            │  Centered 4-signal    │
            │  momentum + recency   │
            │  modulation factor    │
            │  Classification       │
            │  Std-dev explanations │
            └───────────┬───────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │  9. RESULTS STORAGE   │
            │  Write to database    │
            │  (pre-computed)       │
            └───────────────────────┘
```

---

## 2. Module 1: Text Preprocessing

### 2.1 Purpose & Canonical Preprocessing Policy

Social-media text is noisy, containing URLs, handle mentions, hashtags, and inconsistent capitalization. Different downstream NLP tasks have conflicting input representation requirements:
- **Keyword & Vocabulary Extraction (c-TF-IDF, TF-IDF):** Requires lowercased, cleaned text to prevent duplicate vocabulary entries ("Climate" vs "climate").
- **Transformer Sentiment Analysis:** Pretrained specifically on social text with normalized tokens (`@user` for mentions, `http` for links) while preserving expressive capitalization and punctuation.
- **Named Entity Recognition (NER):** Relies heavily on capitalization signals (e.g., "Apple" vs "apple", "Paris" vs "paris"). Lowercasing severely damages NER recall and precision.
- **Auditing & Ground Truth:** The raw unmodified text must remain permanently intact.

#### Canonical Dataset-Level Preprocessing (v1 Policy)
In v1, preprocessing is **canonical at the dataset level**:
1. Preprocessing is dataset-scoped, canonical and immutable for `preprocessing_version="1.0.0"`. It executes once for a dataset when the preprocessing stage is run (Phase 3), before NLP analysis.
2. Distinct `AnalysisRuns` **MUST NOT** overwrite or mutate the `posts` preprocessing columns (`cleaned_text`, `sentiment_ready_text`). Subsequent `AnalysisRuns` reuse the canonical preprocessed representations rather than re-cleaning or overwriting them.
3. For v1, preprocessing configuration is fixed and versioned rather than configurable independently for each `AnalysisRun`. Each dataset records a `preprocessing_version` (e.g., `"1.0.0"`), and every `AnalysisRun` references this version in its configuration metadata to guarantee that results are strictly reproducible without coupling Phase 2 dataset ingestion to Phase 3 NLP preprocessing.

### 2.2 Text Representations

| Representation | Storage | Casing | Mentions | URLs | Target NLP Tasks |
|----------------|---------|--------|----------|------|------------------|
| `original_text` | `posts.original_text` | Untouched | Raw `@username` | Raw URL | Human inspection, raw archive, baseline |
| `cleaned_text` | `posts.cleaned_text` | Lowercased | Stripped or `@user` | Removed | BERTopic embeddings, TF-IDF, c-TF-IDF keywords, text search |
| `sentiment_ready_text` | `posts.sentiment_ready_text` | Preserved | Replaced with `@user` | Replaced with `http` | CardiffNLP Twitter-RoBERTa sentiment classifier |
| *NER representation* | *Derived at runtime* | Preserved | Preserved or stripped | Removed | spaCy NER (`en_core_web_sm`) |

> **Design Decision on `ner_ready_text`:** spaCy NER requires casing preservation and minimal noise. Storing a fourth text column across thousands of posts in the database adds redundant storage for minimal benefit. Instead, the NER representation is derived deterministically at pipeline runtime from `original_text` (HTML unescaping, whitespace collapsing, URL removal, but strictly retaining capitalization and entity punctuation).

### 2.3 Operations (in order)

| Step | Operation | Detail | Target Representation |
|------|-----------|--------|------------------------|
| 1 | **Duplicate detection** | Hash-based deduplication on `original_text`; flag duplicates via `is_duplicate`, do not silently discard. | Metadata |
| 2 | **HTML entity decoding** | Decode `&amp;` → `&`, `&lt;` → `<`, `&gt;` → `>`, etc. | All variants |
| 3 | **Hashtag extraction** | Regex `#(\w+)`: extract into `extracted_hashtags` list (preserving original casing). In `cleaned_text`, strip `#` prefix but retain token. | Side-channel + `cleaned_text` |
| 4 | **Mention extraction & normalization** | Regex `@(\w+)`: extract into `extracted_mentions` list. For `sentiment_ready_text`, substitute `@user`. For `cleaned_text`, replace with `@user` or remove. | Side-channel, `sentiment_ready_text`, `cleaned_text` |
| 5 | **URL extraction & normalization** | Regex URL pattern: extract into `extracted_urls` list. For `sentiment_ready_text`, substitute `http`. For `cleaned_text`, remove entirely. | Side-channel, `sentiment_ready_text`, `cleaned_text` |
| 6 | **Emoji handling** | Convert emojis to text descriptions (e.g., 😀 → `:grinning_face:`) using the `emoji` package, or strip based on configuration. | `cleaned_text` |
| 7 | **Whitespace normalization** | Collapse multiple spaces, newlines, and tabs into a single space. Strip leading/trailing whitespace. | All variants |
| 8 | **Case normalization** | Lowercase applied exclusively to `cleaned_text`. `original_text`, `sentiment_ready_text`, and the NER representation retain original casing. | `cleaned_text` |
| 9 | **Punctuation handling** | Collapse excessive repeated punctuation (e.g., `!!!!!!` → `!`, `????` → `?`). Do not strip sentence-ending punctuation. | `cleaned_text`, `sentiment_ready_text` |

### 2.4 Outputs

| Field | Type | Description |
|-------|------|-------------|
| `original_text` | str | Unmodified input text (stored in `posts`) |
| `cleaned_text` | str | Lowercased, sanitized text for topic modeling and keywords (stored in `posts`) |
| `sentiment_ready_text` | str | Case-preserved text with `@user` and `http` tokens (stored in `posts`) |
| `extracted_hashtags` | list[str] | Hashtags found in the post (stored as JSON in `posts.hashtags`) |
| `extracted_mentions` | list[str] | Mentions found in the post (stored as JSON in `posts.mentions`) |
| `extracted_urls` | list[str] | URLs found in the post (stored as JSON in `posts.urls`) |
| `is_duplicate` | bool | Whether this post is a duplicate (stored in `posts.is_duplicate`) |
| `preprocessing_metadata` | dict | Counts of items removed/normalized, plus `preprocessing_version` |

---

## 3. Module 2: Sentence Embeddings

### 3.1 Model Selection

| Model | Dimensions | Speed | Quality | Size |
|-------|-----------|-------|---------|------|
| **`all-MiniLM-L6-v2`** (default) | 384 | Fast | Good | ~80MB |
| `all-mpnet-base-v2` (optional upgrade) | 768 | Moderate | Better | ~420MB |

**Default choice: `all-MiniLM-L6-v2`** — best balance of speed, quality, and download size for a CPU-only college project.

### 3.2 Batch Processing

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = model.encode(
    texts,
    batch_size=64,
    show_progress_bar=True,
    normalize_embeddings=True
)
```

### 3.3 Reproducibility

- Set `torch` random seed before encoding.
- Store model name and version in `AnalysisRun` metadata.

---

## 4. Module 3: Topic Modeling

### 4.1 Pipeline

```
Embeddings (384-dim)
        │
        ▼
┌───────────────┐
│     UMAP      │  Reduce to 5-dim
│  n_neighbors  │  (configurable)
│  = 15         │
│  min_dist     │
│  = 0.0        │
│  metric       │
│  = cosine     │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│   HDBSCAN     │  Cluster reduced embeddings
│  min_cluster  │
│  _size = 10   │  (configurable)
│  min_samples  │
│  = 5          │
│  metric       │
│  = euclidean  │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│   c-TF-IDF    │  Extract topic representations
│               │  from clustered documents
└───────┬───────┘
        │
        ▼
┌───────────────┐
│ Topic Naming  │  Auto-generate display names
│               │  from top-3 keywords
└───────────────┘
```

### 4.2 BERTopic Configuration

```python
from bertopic import BERTopic
from umap import UMAP
from hdbscan import HDBSCAN
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import CountVectorizer

umap_model = UMAP(
    n_neighbors=15,
    n_components=5,
    min_dist=0.0,
    metric="cosine",
    random_state=42
)

hdbscan_model = HDBSCAN(
    min_cluster_size=10,
    min_samples=5,
    metric="euclidean",
    prediction_data=True
)

vectorizer_model = CountVectorizer(
    stop_words="english",
    ngram_range=(1, 2),
    min_df=2
)

topic_model = BERTopic(
    embedding_model=SentenceTransformer("all-MiniLM-L6-v2"),
    umap_model=umap_model,
    hdbscan_model=hdbscan_model,
    vectorizer_model=vectorizer_model,
    nr_topics=None,          # Preserve natural HDBSCAN clusters without premature reduction
    calculate_probabilities=False,  # Faster; we don't need soft assignments
    verbose=True
)

topics, probs = topic_model.fit_transform(documents, embeddings)
```

> **Topic Reduction Policy:** `nr_topics` is initialized to `None` to preserve HDBSCAN-discovered micro-clusters. If a large dataset yields an excessively fragmented number of topics, topic reduction may optionally be invoked post-hoc via `topic_model.reduce_topics(documents, nr_topics=target_count)`.

### 4.3 Topic Outputs

| Field | Type | Description |
|-------|------|-------------|
| `topic_id` | int | BERTopic topic ID (-1 = outlier) |
| `display_name` | str | Generated from top keywords (e.g., "AI & Machine Learning") |
| `keywords` | list[tuple[str, float]] | Top-10 keywords with c-TF-IDF scores |
| `representative_docs` | list[str] | 5 representative posts |
| `post_count` | int | Number of posts in this topic |
| `sentiment_distribution` | dict | {positive: N, neutral: N, negative: N} |
| `avg_engagement` | dict | {likes: avg, comments: avg, shares: avg} |

### 4.4 Outlier Handling

Posts assigned `topic_id = -1` by HDBSCAN are **preserved as unclassified**. They are:
- Counted in overall statistics.
- Excluded from topic-specific trend scoring.
- Visible in search results.
- Not forced into artificial topics.

### 4.5 Topic Naming Strategy

1. Take top-3 c-TF-IDF keywords for each topic.
2. Capitalize and join: e.g., `["climate", "emissions", "carbon"]` → `"Climate, Emissions & Carbon"`.
3. Store as `display_name` (editable if we later add user-facing controls).

---

## 5. Module 4: Sentiment Analysis

### 5.1 Model

**`cardiffnlp/twitter-roberta-base-sentiment-latest`**

- Architecture: RoBERTa-base fine-tuned on ~124M tweets.
- Labels: `negative` (0), `neutral` (1), `positive` (2).
- Input: Tweet-like text up to 512 tokens (using `sentiment_ready_text`).
- License: CC-BY-4.0.

### 5.2 Implementation

```python
from transformers import AutoModelForSequenceClassification, AutoTokenizer, AutoConfig
import torch
import numpy as np

class SentimentAnalyzer:
    MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment-latest"
    LABELS = ["negative", "neutral", "positive"]
    
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained(self.MODEL_NAME)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.MODEL_NAME)
        self.model.eval()
    
    def predict_batch(self, texts: list[str], batch_size: int = 32) -> list[dict]:
        results = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            inputs = self.tokenizer(
                batch, 
                return_tensors="pt", 
                padding=True, 
                truncation=True, 
                max_length=512
            )
            with torch.no_grad():
                outputs = self.model(**inputs)
            probs = torch.softmax(outputs.logits, dim=1).numpy()
            for prob in probs:
                label_idx = np.argmax(prob)
                results.append({
                    "label": self.LABELS[label_idx],
                    "confidence": float(prob[label_idx]),
                    "scores": {
                        self.LABELS[j]: float(prob[j]) for j in range(3)
                    }
                })
        return results
```

### 5.3 Preprocessing Alignment

The `twitter-roberta-base` model expects:
- `@user` tokens for mentions (not original usernames).
- `http` for URLs (not full URLs).

Our preprocessing must produce a **sentiment-ready** variant of cleaned text that aligns with these expectations.

### 5.4 Outputs

| Field | Type | Description |
|-------|------|-------------|
| `sentiment_label` | str | `positive`, `neutral`, or `negative` |
| `confidence` | float | Confidence of the predicted label (0–1) |
| `scores` | dict[str, float] | Probability for each class |

### 5.5 Evaluation (conditional)

If the dataset contains a ground-truth `sentiment` column, compute:

| Metric | Description |
|--------|-------------|
| Accuracy | Overall correct predictions / total |
| Precision | Per-class precision |
| Recall | Per-class recall |
| F1-Score | Per-class and macro-averaged F1 |
| Confusion Matrix | 3×3 matrix (positive/neutral/negative) |

These metrics are **only computed when ground-truth labels exist**. They are never fabricated.

---

## 6. Module 5: Keyword & Hashtag Extraction

### 6.1 Hashtag Analysis

| Metric | Computation |
|--------|-------------|
| **Frequency** | Count occurrences across all posts |
| **Growth rate** | `(count_current_window - count_previous_window) / count_previous_window` |
| **Topic association** | Which topics each hashtag appears in |
| **Temporal distribution** | Hashtag usage over time buckets |

### 6.2 Keyword Extraction

Two complementary approaches:

#### a) c-TF-IDF Keywords (topic-level)
Extracted automatically by BERTopic. Top-N keywords per topic with c-TF-IDF scores.

#### b) Corpus-level TF-IDF Keywords
```python
from sklearn.feature_extraction.text import TfidfVectorizer

vectorizer = TfidfVectorizer(
    max_features=500,
    ngram_range=(1, 3),
    stop_words="english",
    min_df=2,
    max_df=0.95
)
tfidf_matrix = vectorizer.fit_transform(cleaned_texts)
```

#### c) Temporal Keyword Growth

For each time window, compute keyword frequency and calculate growth:

```
growth_rate = (freq_current - freq_previous) / max(freq_previous, 1)
```

A keyword is "trending" if `growth_rate > threshold` AND `freq_current > min_frequency`.

### 6.3 Outputs

| Field | Type | Description |
|-------|------|-------------|
| `keyword` | str | The keyword or n-gram |
| `frequency` | int | Total occurrences |
| `tfidf_score` | float | TF-IDF importance score |
| `growth_rate` | float | Change vs previous window |
| `associated_topics` | list[int] | Topic IDs this keyword appears in |

---

## 7. Module 6: Named Entity Recognition

### 7.1 Model

**spaCy `en_core_web_sm`** (default) — lightweight, fast, suitable for batch NER on social-media text.

Optional upgrade: `en_core_web_trf` (transformer-based, higher accuracy, ~500MB download).

### 7.2 Entity Types

| spaCy Label | Our Label | Examples |
|-------------|-----------|----------|
| `PERSON` | Person | Elon Musk, Taylor Swift |
| `ORG` | Organization | Google, WHO, FIFA |
| `GPE` | Location | New York, India, Paris |
| `PRODUCT` | Product | iPhone, ChatGPT |
| `EVENT` | Event | Olympics, COP28 |
| `NORP` | Group | Democrats, European Union |

### 7.3 Processing

> **Case-Preservation Requirement for NER:** spaCy's statistical NER model (`en_core_web_sm`) relies heavily on capitalization features to recognize proper nouns, companies, locations, and personal names. Lowercased text severely degrades NER accuracy. Therefore, NER operates on a **case-preserving representation derived deterministically at runtime from `original_text`** (HTML entities unescaped, whitespace normalized, raw URLs stripped/masked, but original capitalization and punctuation intact). It does not use lowercased `cleaned_text`.

```python
import spacy

nlp = spacy.load("en_core_web_sm", disable=["parser", "lemmatizer"])

def derive_ner_text(original_text: str) -> str:
    """Deterministically derive clean, case-preserved text for NER from original_text."""
    import html, re
    text = html.unescape(original_text)
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_entities(texts: list[str]) -> list[list[dict]]:
    results = []
    # texts passed here are case-preserved strings derived via derive_ner_text
    for doc in nlp.pipe(texts, batch_size=100):
        entities = []
        for ent in doc.ents:
            if ent.label_ in {"PERSON", "ORG", "GPE", "PRODUCT", "EVENT", "NORP"}:
                entities.append({
                    "text": ent.text,
                    "label": ent.label_,
                    "start": ent.start_char,
                    "end": ent.end_char
                })
        results.append(entities)
    return results
```

### 7.4 Entity Aggregation

| Metric | Description |
|--------|-------------|
| **Frequency** | How often each entity appears across posts |
| **Growth** | Entity frequency change over time windows |
| **Topic association** | Which topics mention this entity |
| **Co-occurrence** | Which entities frequently appear together |

### 7.5 Social Media Challenges

Social-media NER is noisy. Mitigations:
- Filter entities with length < 2 characters.
- Merge variants: case-insensitive dedup (e.g., "google" = "Google").
- Ignore entities that are common words (e.g., "Will" as a name vs. modal verb).

---

## 8. Module 7: Temporal Aggregation

### 8.1 Time Windows & UTC Normalization Policy

All imported post timestamps are normalized to **UTC** during ingestion and stored as UTC timestamps in the database (`posts.timestamp`). 

Before bucketing into time windows, the temporal aggregation module strictly verifies and enforces UTC timezone awareness:
1. Every timestamp is normalized to UTC (`dt.astimezone(timezone.utc)`).
2. Time-window boundaries (`window_start`, `window_end`) are computed on UTC calendar boundaries (e.g., UTC midnight `00:00:00Z` for daily windows, UTC top-of-hour `:00:00Z` for hourly windows).
3. Window comparison compares the current UTC window against the immediately preceding comparable UTC window.

| Window | Bucket Size | Comparison | UTC Boundary Example |
|--------|-------------|------------|----------------------|
| Hourly | 1 hour | Current hour vs previous hour | `2026-07-15T14:00:00Z` to `2026-07-15T14:59:59Z` |
| Daily | 1 day | Current day vs previous day | `2026-07-15T00:00:00Z` to `2026-07-15T23:59:59Z` |
| Weekly | 7 days | Current week vs previous week | Monday `00:00:00Z` to Sunday `23:59:59Z` |

### 8.2 Aggregation Per Bucket

For each `(topic, time_bucket)` pair in UTC, compute:

| Metric | Formula |
|--------|---------|
| `post_count` | Number of posts in this bucket |
| `avg_sentiment` | Mean sentiment score |
| `sentiment_distribution` | {pos: N, neu: N, neg: N} |
| `total_likes` | Sum of likes |
| `total_comments` | Sum of comments |
| `total_shares` | Sum of shares |
| `avg_engagement` | (likes + comments + shares) / post_count |
| `unique_authors` | Distinct authors in this bucket |

### 8.3 Window Comparison

```python
def compare_windows(current: dict, previous: dict) -> dict:
    """Compare two UTC time-window aggregations."""
    def safe_growth(curr, prev):
        if prev == 0:
            return float('inf') if curr > 0 else 0.0
        return (curr - prev) / prev
    
    return {
        "volume_growth": safe_growth(current["post_count"], previous["post_count"]),
        "engagement_growth": safe_growth(current["avg_engagement"], previous["avg_engagement"]),
        "sentiment_shift": current["avg_sentiment"] - previous["avg_sentiment"],
    }
```

---

## 9. Module 8: Trend Detection Engine

### 9.1 Philosophy & Design Principles

A **trend** is NOT simply the most frequent topic. A trend represents **abnormal or rapidly increasing attention**. 
Key design requirements:
1. **Neutrality of Zero Growth:** A topic with no volume growth, no engagement change, zero velocity, and normal historical baseline activity ($z=0$) must be mathematically neutral ($M_{\text{base}} = 0.50$, $\text{TrendScore} = 0.50$) and classify as **Stable**.
2. **Recency as Modulation, NOT Growth:** Recency must not be an additive growth signal. Recency reflects signal freshness/relevance — it modulates momentum deviation from neutral. High recency on a zero-growth topic must NEVER turn it into a rising trend.
3. **Centered Logistic Normalization:** All growth and momentum signals are normalized via centered logistic normalization (logistic normalization with 0.5 as the neutral point) mapping $(-\infty, +\infty) \to (0, 1)$ where an input of $0$ maps to exactly $0.5$ (neutral). Do not refer to this function as a "signed sigmoid" since its output domain is $[0, 1]$:
   - Negative signal $\to$ normalized value $< 0.5$ (contraction / decelerating / below baseline)
   - Zero signal $\to$ normalized value $= 0.5$ (neutral / steady state)
   - Positive signal $\to$ normalized value $> 0.5$ (positive growth / accelerating / burst)

### 9.2 The 4 Core Momentum Signals

#### Signal 1: Volume Growth ($g_v$, default weight: 0.35)
Measures relative change in post count between consecutive windows:
```
volume_growth = (V_current - V_previous) / max(V_previous, min_baseline)
norm_volume_growth = logistic_normalize(volume_growth, k=1.0)
```
Where `min_baseline` (default: 1.0) prevents division-by-zero for new topics.

#### Signal 2: Engagement Growth ($g_e$, default weight: 0.25)
Measures relative change in average interactions per post:
```
E_current = avg(likes + comments + shares) in current window
E_previous = avg(likes + comments + shares) in previous window
engagement_growth = (E_current - E_previous) / max(E_previous, 1.0)
norm_engagement_growth = logistic_normalize(engagement_growth, k=1.0)
```

*Missing Engagement vs Genuine Zero Engagement:*
- **Unavailable / Unmapped Engagement Fields:** If the dataset lacks engagement metrics (columns unmapped in `dataset.column_mapping`), $w_{\text{eng}}$ is set to 0 and its weight (0.25) is redistributed proportionally across volume growth, velocity, and burstiness ($w_v = 0.467, w_{\text{vel}} = 0.267, w_b = 0.266$). Never fabricate missing engagement metrics.
- **Genuine Zero Engagement:** If engagement fields are available and mapped in the dataset, but posts legitimately have `likes = 0, comments = 0, shares = 0`, zero is treated as a valid engagement measurement. The engagement signal remains active ($E_{\text{current}} = 0, E_{\text{previous}} = 0 \implies g_e = 0 \implies \text{logistic\_normalize}(0) = 0.50$), and its weight is NOT redistributed.

#### Signal 3: Velocity ($v$, default weight: 0.20)
Measures acceleration — whether volume growth itself is increasing or decelerating:
```
velocity = volume_growth_current - volume_growth_previous
norm_velocity = logistic_normalize(velocity, k=1.0)
```
Positive velocity indicates accelerating attention; negative velocity indicates deceleration even if post volume remains positive.

#### Signal 4: Burstiness ($z_b$, default weight: 0.20)
Measures how abnormal the current window's volume is compared to the historical baseline:
```
burst_score = (V_current - historical_mean) / max(historical_std, 1.0)
norm_burst = logistic_normalize(burst_score, k=0.5)
```
This is a standard statistical **z-score**: the number of standard deviations the current volume deviates from historical average. An input of $z=0$ (normal baseline volume) maps to $0.50$ (neutral).

### 9.3 Centered Logistic Normalization Function

```python
import math

def logistic_normalize(x: float, k: float = 1.0) -> float:
    """
    Centered logistic normalization mapping any real number to (0, 1) with 0.5 as neutral point.
    x < 0 maps to (0.0, 0.5) (contraction / decelerating / below baseline).
    x = 0 maps to exactly 0.5 (neutral / no change).
    x > 0 maps to (0.5, 1.0) (positive growth / accelerating / burst).
    k controls the sensitivity/steepness.
    """
    return 1.0 / (1.0 + math.exp(-k * x))
```

### 9.4 Base Momentum Score ($M_{\text{base}}$)

The 4 normalized signals are combined using normalized weights summing to 1.0:

```python
def compute_base_momentum(
    norm_vol: float,
    norm_eng: float,
    norm_vel: float,
    norm_burst: float,
    has_engagement: bool = True
) -> float:
    """
    Compute base momentum.
    has_engagement is True if engagement fields were supplied/mapped in the dataset.
    If engagement fields were omitted, weight is redistributed proportionally.
    If engagement fields were mapped but all values are 0, has_engagement remains True.
    """
    if has_engagement:
        w_vol, w_eng, w_vel, w_burst = 0.35, 0.25, 0.20, 0.20
    else:
        # Redistribute engagement weight proportionally: 0.35/0.75, 0.20/0.75, 0.20/0.75
        w_vol, w_eng, w_vel, w_burst = 0.467, 0.0, 0.267, 0.266
    
    return (w_vol * norm_vol) + (w_eng * norm_eng) + (w_vel * norm_vel) + (w_burst * norm_burst)
```

**Neutrality property:** When all inputs are zero ($g_v = 0, g_e = 0, v = 0, z_b = 0$), each normalized signal is exactly $0.50$, so:
$$M_{\text{base}} = 0.35(0.5) + 0.25(0.5) + 0.20(0.5) + 0.20(0.5) = 0.50$$

### 9.5 Recency as a Relevance / Modulation Factor

Recency quantifies how fresh the activity is, modeled as an exponential decay:
```python
hours_since_last_post = max(0.0, (now_utc - latest_post_time_utc).total_seconds() / 3600.0)
recency_factor = math.exp(-decay_rate * hours_since_last_post)  # in (0.0, 1.0]
```
Where `decay_rate` (default: 0.05 for daily windows, 0.1 for hourly) controls how rapidly old activity fades.

**Modulation Formula:**
$$\text{TrendScore} = 0.5 + (M_{\text{base}} - 0.5) \times \text{recency\_factor}$$

#### Mathematical Guarantee
- If a topic has **zero growth** ($M_{\text{base}} = 0.50$), then $(M_{\text{base}} - 0.50) = 0.0$.
- $\text{TrendScore} = 0.50 + (0.0) \times \text{recency\_factor} = \mathbf{0.50}$, regardless of whether the latest post occurred 1 minute ago or 1 month ago.
- If a topic is **actively growing** ($M_{\text{base}} = 0.85$):
  - If fresh ($\text{recency\_factor} = 1.0$): $\text{TrendScore} = 0.5 + 0.35 \times 1.0 = \mathbf{0.85}$ (strong trend).
  - If old/dormant ($\text{recency\_factor} = 0.20$): $\text{TrendScore} = 0.5 + 0.35 \times 0.20 = \mathbf{0.57}$ (momentum has decayed towards neutral).
- If a topic is **actively declining** ($M_{\text{base}} = 0.20$):
  - If fresh ($\text{recency\_factor} = 1.0$): $\text{TrendScore} = 0.5 + (-0.30) \times 1.0 = \mathbf{0.20}$ (strong decline).

### 9.6 Trend Classification

| Classification | Condition | Description | Icon |
|---------------|-----------|-------------|------|
| **Emerging** | `TrendScore ≥ 0.70` AND (`topic_age_windows < 2` OR `volume_previous == 0`) AND `volume_current ≥ min_posts` | Brand new topic spiking sharply from near-zero baseline | 🔥 |
| **Rising** | `TrendScore ≥ 0.60` | Established topic experiencing significant acceleration and positive attention | ↗ |
| **Stable** | `0.40 ≤ TrendScore < 0.60` | Normal, baseline, or zero-growth activity (neutral 0.50 falls squarely in center) | → |
| **Declining** | `TrendScore < 0.40` | Contracting topic with negative volume/engagement growth | ↘ |

### 9.7 Trend Explanation Generation

Each trend explanation is built from actual computed statistics. **Burst z-scores are strictly described in terms of standard deviations**, not as multiplicative ratios:

```python
def generate_explanation(metrics: dict) -> str:
    parts = []
    
    vg = metrics["volume_growth_pct"]
    if vg > 15:
        parts.append(f"Post volume increased by {vg:.0f}% compared to the previous period")
    elif vg < -15:
        parts.append(f"Post volume decreased by {abs(vg):.0f}% compared to the previous period")
    
    eg = metrics["engagement_growth_pct"]
    if eg > 15:
        parts.append(f"engagement grew by {eg:.0f}%")
    elif eg < -15:
        parts.append(f"engagement dropped by {abs(eg):.0f}%")
    
    bs = metrics["burst_score"]  # Statistical z-score: (V_current - mean) / std
    if bs >= 2.0:
        parts.append(f"activity is {bs:.1f} standard deviations above the historical baseline")
    elif bs <= -2.0:
        parts.append(f"activity is {abs(bs):.1f} standard deviations below the historical baseline")
        
    vel = metrics.get("velocity", 0.0)
    if vel > 0.5:
        parts.append("growth is accelerating")
    elif vel < -0.5:
        parts.append("growth is slowing down")
    
    if not parts:
        parts.append("Activity levels and engagement remain consistent with historical norms")
    
    return ". ".join(parts) + "."
```

*Example Output:*  
`"Post volume increased by 118% compared to the previous period. Engagement grew by 42%. Activity is 3.2 standard deviations above the historical baseline. Growth is accelerating."`

### 9.8 Deterministic Edge Cases & Test Scenarios

The trend engine must deterministically pass the following test scenarios:

| Scenario | Input Conditions | Expected Behavior | Expected Classification |
|----------|------------------|-------------------|--------------------------|
| **1. No-Growth Case** | $V_{\text{current}} = 50$, $V_{\text{prev}} = 50$, $E_{\text{curr}} = 10$, $E_{\text{prev}} = 10$, $v = 0$, $z_b = 0$, latest post = 5 min ago ($R = 1.0$) | $g_v = 0, g_e = 0, v = 0, z_b = 0 \implies M_{\text{base}} = 0.50$, $\text{TrendScore} = 0.50$ | **Stable** (not Rising) |
| **2. Rising Case** | $V_{\text{curr}} = 120$, $V_{\text{prev}} = 40$ ($+200\%$), $E_{\text{curr}} = 25$, $E_{\text{prev}} = 15$, $v > 0$, $z_b = 2.8$, recent post ($R = 0.95$) | $M_{\text{base}} > 0.75$, $\text{TrendScore} \ge 0.60$ | **Rising** |
| **3. Declining Case** | $V_{\text{curr}} = 20$, $V_{\text{prev}} = 80$ ($-75\%$), $E_{\text{curr}} = 4$, $E_{\text{prev}} = 16$, $v < 0$, $z_b = -2.1$, recent post ($R = 0.90$) | $M_{\text{base}} < 0.30$, $\text{TrendScore} < 0.40$ | **Declining** |
| **4. Emerging-from-Zero Case** | $V_{\text{prev}} = 0$, $V_{\text{curr}} = 35$, topic age = 1 window, recent post ($R = 1.0$) | Safe baseline division via $\text{min\_baseline}$, $M_{\text{base}} > 0.80$, $\text{TrendScore} \ge 0.70$ | **Emerging** |
| **5A. Missing Engagement Case (Fields Unavailable)** | Engagement metrics unmapped / omitted in dataset (`has_engagement=False`) | Engagement signal omitted ($w_{\text{eng}} = 0$), weight redistributed proportionally ($w_v=0.467, w_{\text{vel}}=0.267, w_b=0.266$); no NaN/ZeroDivision errors; no fabricated metrics | Dependent on volume dynamics |
| **5B. Genuine Zero Engagement Case (Fields Available)** | Engagement fields mapped in dataset, but all interactions are zero (`likes=0, comments=0, shares=0`) | Zero is treated as valid measurement; $g_e = 0 \implies \text{logistic\_normalize}(0) = 0.50$; $w_{\text{eng}} = 0.25$ remains active; no weight redistribution | Consistent with neutral engagement |
| **6. Tiny-Sample Case** | Total posts in topic = 2 (< `min_posts_for_trend`) | Zero-division guarded, low-confidence flag set, avoided spurious Emerging/Rising classification | **Stable** / Unranked |

### 9.9 Configuration

```python
@dataclass
class TrendConfig:
    weight_volume: float = 0.35
    weight_engagement: float = 0.25
    weight_velocity: float = 0.20
    weight_burstiness: float = 0.20
    
    min_baseline: float = 1.0
    decay_rate: float = 0.05
    logistic_k: float = 1.0
    burst_logistic_k: float = 0.5
    
    threshold_emerging: float = 0.70
    threshold_rising: float = 0.60
    threshold_stable: float = 0.40
    
    min_posts_for_trend: int = 3
    time_window: str = "daily"  # hourly, daily, weekly
```

---

## 10. Pipeline Orchestration

### 10.1 Execution Order & Task Representations

```python
class NLPPipeline:
    def run(self, dataset_id: str, config: PipelineConfig, db_session) -> AnalysisRun:
        run = self.create_analysis_run(dataset_id, config)
        posts = self.load_posts(dataset_id)
        
        # Step 1: Preprocess check (canonical at dataset level)
        self.update_progress(run, "preprocessing", 5)
        # Verify canonical preprocessed texts exist; if not yet run, preprocess once for dataset
        if not posts[0].cleaned_text:
            self.preprocessor.process_dataset(dataset_id, version="1.0.0")
            posts = self.load_posts(dataset_id)
            
        cleaned_texts = [p.cleaned_text for p in posts]
        sentiment_texts = [p.sentiment_ready_text for p in posts]
        ner_texts = [derive_ner_text(p.original_text) for p in posts]  # Case-preserved runtime text
        
        # Step 2: Embeddings (uses cleaned_texts)
        self.update_progress(run, "embeddings", 15)
        embeddings = self.embedder.encode(cleaned_texts)
        
        # Step 3: Topic modeling (BERTopic with nr_topics=None, uses cleaned_texts)
        self.update_progress(run, "topic_modeling", 35)
        topics = self.topic_modeler.fit_transform(cleaned_texts, embeddings)
        self.save_topics(run, topics)
        
        # Step 4: Sentiment analysis (uses sentiment_texts)
        self.update_progress(run, "sentiment", 55)
        sentiments = self.sentiment_analyzer.predict_batch(sentiment_texts)
        self.save_sentiments(run, sentiments)
        
        # Step 5: NER (uses case-preserved ner_texts)
        self.update_progress(run, "ner", 70)
        entities = self.ner.extract(ner_texts)
        self.save_entities(run, entities)
        
        # Step 6: Keywords & hashtags (uses cleaned_texts + extracted hashtags)
        self.update_progress(run, "keywords", 80)
        keywords = self.keyword_extractor.extract(posts, topics)
        self.save_keywords(run, keywords)
        
        # Step 7: Temporal aggregation (strictly UTC-normalized)
        self.update_progress(run, "temporal", 88)
        temporal = self.temporal_aggregator.aggregate(posts, topics, config.time_window)
        
        # Step 8: Trend detection (centered logistic normalization + recency modulation)
        self.update_progress(run, "trends", 95)
        trends = self.trend_scorer.score(temporal, config.trend_config)
        self.save_trends(run, trends)
        
        # Done
        self.update_progress(run, "completed", 100)
        return run
```

### 10.2 Model Registry

Track all models used for reproducibility:

```python
MODEL_REGISTRY = {
    "embedding": {
        "name": "all-MiniLM-L6-v2",
        "source": "sentence-transformers",
        "dimensions": 384,
    },
    "sentiment": {
        "name": "cardiffnlp/twitter-roberta-base-sentiment-latest",
        "source": "huggingface-transformers",
        "license": "CC-BY-4.0",
        "training": "~124M tweets",
        "labels": ["negative", "neutral", "positive"],
    },
    "ner": {
        "name": "en_core_web_sm",
        "source": "spacy",
        "entity_types": ["PERSON", "ORG", "GPE", "PRODUCT", "EVENT", "NORP"],
        "input_casing": "case-preserved",
    },
    "topic_modeling": {
        "name": "BERTopic",
        "source": "bertopic",
        "nr_topics": None,
        "sub_models": {
            "umap": {"n_neighbors": 15, "n_components": 5, "min_dist": 0.0, "random_state": 42},
            "hdbscan": {"min_cluster_size": 10, "min_samples": 5},
            "vectorizer": {"ngram_range": [1, 2], "stop_words": "english"},
        }
    }
}
```

---

## 11. Performance Considerations

| Concern | Mitigation |
|---------|------------|
| Sentiment inference is slow on CPU | Batch inference (32 texts/batch); consider ONNX Runtime export for 2-3× speedup if needed |
| Embedding computation | Batch encode with `sentence-transformers` (64 texts/batch); embeddings computed once, reused |
| BERTopic on small datasets | If <50 posts, warn user and reduce `min_cluster_size` |
| spaCy NER throughput | Use `nlp.pipe()` with batching; disable unused components (parser, lemmatizer) |
| Memory | Models loaded once at startup (lazy-loaded on first analysis); ~2GB total RAM for all models |

---

## 12. Modularity & Replaceability

Each NLP module follows a common interface pattern:

```python
from abc import ABC, abstractmethod

class BaseSentimentAnalyzer(ABC):
    @abstractmethod
    def predict_batch(self, texts: list[str], batch_size: int = 32) -> list[dict]:
        ...
    
    @abstractmethod
    def model_info(self) -> dict:
        ...

class TwitterRobertaSentiment(BaseSentimentAnalyzer):
    """Default implementation using cardiffnlp/twitter-roberta-base-sentiment-latest"""
    ...

# Future: could swap in a different model
class VaderSentiment(BaseSentimentAnalyzer):
    """Alternative lightweight rule-based approach"""
    ...
```

This pattern is recommended but not mandatory for v1. The primary requirement is that each module lives in its own file/package and can be replaced without touching other modules.
