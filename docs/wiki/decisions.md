# Decisions (ADRs, short form)

Each entry: chosen, why, when. Prune when superseded. Order by date in reverse chronological order.

## 2026-10-18

### 32k context window
- Chosen: `SENTINEL_NUM_CTX=32768` for the agent (Modelfile `docs/Modelfile.32k`).
- Why: enough for a dbt/SQL diff + retrieved context + a structured `Review`; local 27B runs
  within limits. Measured, not guessed.
- Revisit: 16k/32k/64k/128k sweep in M6, decide by eval quality vs. latency/memory.

### Deterministic lineage, LLM explains only
- Chosen: sqlglot + dbt manifest compute lineage/schema diff; the LLM only interprets.
- Why: lineage must be exact and auditable; an LLM guessing joins/producers is unsafe.

### Dry-run PR comments
- Chosen: `review` is dry-run by default; posting needs `--post` + human approval.
- Why: avoid spamming or auto-editing upstream without a human in the loop.

### Knowledge base = files, not chat
- Chosen: `CONTINUE.md` (always loaded) + `docs/STATE.md` (handoff) + `docs/wiki/*` (on demand).
- Why: sessions are short under 32k; curated files give continuity cheaply. A wrong note is worse
  than a missing one, so review model edits, cap sizes, and lint in pre-commit.

### Local only
- Chosen: no cloud LLM calls, no telemetry. Ollama runs everything.
- Why: privacy-first is the product's core promise.
