# Eval

Executed knowledge that can't go stale silently: the seeded-bug eval (`bugs/bugs.yaml`) and the
golden questions (`evals/golden_questions.yaml`).

- Run after any retrieval, chunking, or agent change. They are the guardrails for regressions.
- Benchmarks land here after M3 (hybrid/rerank) and M6 (GitHub integration), then link them into
  `README.md`.
- Open: no benchmark numbers yet (pre-M3). Decide 16k/32k/64k/128k window sweep here in M6.

See also [decisions.md](decisions.md) for the 32k context choice.
