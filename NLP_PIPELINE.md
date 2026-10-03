# Implemented NLP methodology

## Representations and stages

1. Ingestion preserves source text, parses timestamps to UTC and keeps unavailable engagement as NULL. Duplicate text is retained with a flag. Optional mapped hashtags survive preprocessing.
2. Versioned preprocessing produces `cleaned_text` for embeddings/TF-IDF and case-preserved `sentiment_ready_text` with URL/mention placeholders for sentiment. Original text remains queryable. All posts must carry the matching preprocessing version before a run reuses them.
3. CardiffNLP Twitter-RoBERTa sentiment runs locally on CPU in batches of 32, truncating inputs at 128 tokens. It emits positive/neutral/negative probabilities, maximum-score label and confidence. Missing weights fail the run; there is no heuristic substitute.
4. SentenceTransformers all-MiniLM-L6-v2 emits normalized 384-dimensional vectors in batches of 64. Missing weights fail the run; no hash/random-vector substitute exists.
5. For at least 15 posts, BERTopic uses UMAP (`random_state=42`, cosine distance), HDBSCAN and c-TF-IDF unigrams/bigrams. Minimum cluster size is approximately 2% of the corpus with an eight-post floor, bounded for smaller corpora; minimum samples is three. There is no fixed cluster count. Complete-link semantic centroid similarity ≥ .90 consolidates near duplicates without chains of loosely related clusters. Original cluster IDs and terms are recorded separately from display names.
6. Below 15 posts, cosine/average-link agglomerative clustering uses distance threshold .35 and corpus TF-IDF terms. This method is explicitly recorded. Its assignment indicator of 1.0 is not a calibrated probability. BERTopic exceptions fail rather than silently replacing clustering.
7. Display labels use locally derived keyword vocabulary, redundant-stem cleanup and short term descriptors to distinguish clusters in the same family. They never use a remote LLM. Outliers remain explicitly unclassified. A display label is an interpretation, not evidence that the model found one canonical real-world topic.
8. Optional spaCy en_core_web_sm NER operates on case-preserved text without hashtag tokens; allowed types are PERSON, ORG, GPE, PRODUCT, EVENT and NORP. It normalizes whitespace/case and filters generic common nouns and accidental lowercase person spans. If weights are absent, entities are omitted and run metadata/UI expose degraded completion. No capitalization heuristic generates PRODUCT labels.
9. Corpus TF-IDF keywords and hashtag frequencies are distinct from per-topic c-TF-IDF terms. Representative post samples do not limit whole-topic aggregates.

## Temporal scoring

UTC hourly, daily and weekly calendar buckets include zero-activity gaps through the dataset's greatest timestamp. Volume growth, engagement growth, velocity and burst z-score are normalized around the no-growth midpoint 0.5 with centered logistic functions. Burst is measured in standard deviations above/below baseline. The clock is the dataset reference time; historical uploads are not decayed against wall-clock today.

`M = .35 × normalized_volume + .25 × normalized_engagement + .20 × normalized_velocity + .20 × normalized_burst`

`TrendScore = .50 + (M − .50) × recency`

Recency modulates deviation from neutral; it is not an additive signal or a simple product of momentum. No growth remains 0.50 irrespective of age. Missing engagement redistributes .25 proportionally among the other signals; a genuine measured zero is retained. Sentiment does not enter the score.

Classification order: fewer than three current posts → Stable; score ≥ .70 with topic age below two buckets or zero previous activity → Emerging; otherwise ≥ .60 → Rising, ≥ .40 → Stable, else Declining. The minimum-volume guard can legitimately produce a high score with Stable classification. Both explanation and UI disclose it. Current inactivity can therefore be Stable under the guard rather than Declining. There is no Burst class.

Reads recompute hourly/weekly/platform views from stored run-scoped assignments using the same scorer. Stored daily snapshots document the original unfiltered analysis. A maximum of 20,000 buckets limits accidental huge requests; select daily or weekly for long date ranges.

## Evidence and limitations

Run metadata records actual method, cluster parameters, package versions, device, NER availability, weights and reference timestamp. Some library configurations do not expose a model revision; an unknown revision is not invented. Fixed seeds improve repeatability but learned clustering can vary across platforms/library versions. English model bias, truncation, synthetic wording and imperfect entity boundaries remain important limits. No sentiment accuracy or general-domain topic accuracy is claimed from unlabeled CSVs. See `docs/MODEL_EVALUATION.md` and `docs/NLP_SMOKE_EVIDENCE.json` for executed synthetic smoke evidence.
