# Academic report and viva notes

Use the implemented workflow and audit evidence as the source of truth. Do not describe historical roadmap phases as proof that all acceptance criteria passed.

## Suggested report structure

1. Problem: social-media datasets contain evolving topics and sentiment; volume alone cannot explain change.
2. Scope: English CSV batches, local CPU inference, user-reviewed validation, explicit dataset/run selection. Explain why live integrations and distributed infrastructure are outside this college-project scope.
3. Data: deterministic 900-post/21-day/three-platform/five-theme demo and separately uploaded custom CSV. Disclose synthetic source intent and duplicate policy; do not present generated labels as independent evaluation annotations.
4. Architecture: Next.js → thin FastAPI routes → scoped services → SQLAlchemy/SQLite or PostgreSQL → in-process worker/local NLP. Explain UUID staging, transactional imports, cascade deletion, one active run and interruption recovery.
5. Methods: immutable text representations, RoBERTa sentiment, MiniLM embeddings, seeded UMAP/HDBSCAN/c-TF-IDF, conservative topic consolidation, explicit small-corpus clustering, optional spaCy degradation, keywords/hashtags and UTC trend scoring.
6. Mathematics: centered logistic signals; weighted momentum .35/.25/.20/.20; `TrendScore = .5 + (M − .5) × recency`; missing-engagement weight redistribution; three-post Stable guard and four classifications. Sentiment is contextual evidence and is not a score component.
7. Results: quote only executed evidence in `CODEX_AUDIT.md` and `NLP_SMOKE_EVIDENCE.json`. Distinguish deterministic fixture integration from real-model smoke. Show a topic's original posts, raw keywords, full history and explanation, not only summary totals.
8. Limitations: small synthetic corpus/template artifacts, English model/domain bias, input truncation, imperfect named entities, platform-dependent clustering, single-server process and unsupported ground-truth accuracy claims. PostgreSQL 16.14 runtime was verified on 2026-10-04 with temporary synthetic data; populated production-data rollbacks and physical-device accessibility were not tested. Use the audit's actual evidence boundaries.

## Demo walkthrough

Add Dataset → upload once → preview → map → validate one deliberately invalid timestamp → inspect retained duplicates → confirm import → Run Analysis → progress/history → Open Dashboard → change time window/platform → investigate a ranked topic → inspect exact activity data and representative posts → Explorer keyword/date filters → Analysis model status and formula. Then demonstrate Use Demo Dataset as the secondary path. A failed core model or missing optional NER must be explained honestly.

## Claims to avoid

No invented sentiment accuracy, NER precision, posts-per-second throughput, five exact learned topics, continuous live monitoring, production deployment readiness or universal topic interpretation. MIT covers repository code; downloaded models retain their own licenses. Use the official model cards and cite research references independently when writing the dissertation.
