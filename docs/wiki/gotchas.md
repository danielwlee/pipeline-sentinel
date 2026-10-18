# Gotchas (lessons learned)

One line each: symptom -> cause -> fix. Add on every correction or bug. Prune stale/contradictory.

- Ollama can truncate silently near the context limit -> looks like "forgetting" -> keep
  `SENTINEL_NUM_CTX` headroom and watch logs for truncation.
- `gh pr create --milestone` wants the milestone **title**, not the number -> passing the number
  fails with "not found" -> pass e.g. `"M0: Sanity check"`; re-list with
  `gh api "repos/danielwlee/pipeline-sentinel/milestones"` first.
- Reranker may not work with a community model -> verify in M3, fall back to sentence-transformers.
- A wrong wiki note is worse than a missing one -> review diffs to the wiki, cap page sizes, and
  lint relative links so stale pointers don't accumulate.
- `.git` and Ollama log errors can leak into generated notes -> keep logs out of wiki pages.
