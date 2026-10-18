# Wiki index

On-demand notes for short sessions. Keep each page small (~1k tokens) and single-topic.
Read this first, then open only the page the task needs.

- [decisions.md](decisions.md) — short ADRs: what was chosen and why.
- [gotchas.md](gotchas.md) — lessons learned: symptom -> cause -> fix.
- [eval.md](eval.md) — how the seeded-bug + golden-question evals work.
- [chunking.md](chunking.md) — chunk strategy and retrieval tuning.

Guardrails: cap page sizes, lint relative links (see `scripts/lint_docs.py`), and review the
model's edits to these files — a wrong note is worse than a missing one.
