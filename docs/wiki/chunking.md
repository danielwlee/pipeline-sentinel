# Chunking

One chunk per dbt model for M1. Rationale and tuning notes go here.

- Ingest: dbt `manifest.json` + sqlglot chunker produces one chunk per model (M1).
- Hybrid retrieval is LanceDB vectors + BM25, then a reranker (M2/M3).
- Open: chunk size / overlap not yet tuned; revisit when eval numbers exist (see [eval.md](eval.md)).

See also [decisions.md](decisions.md) for "deterministic lineage, LLM explains only".
