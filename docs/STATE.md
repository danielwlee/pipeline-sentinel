# Project state

Last updated: 2026-10-18

## Current milestone
M0: sanity check. Scaffold is done; a file-based knowledge base now backs short sessions.

## Done
- Repo scaffolded with bootstrap.sh (uv, Typer stubs, Pydantic schemas, bugs.yaml, golden questions, CI)
- Decision: agent context is 32k (`SENTINEL_NUM_CTX`); revisit with a 16k/32k/64k/128k eval in M6
- Knowledge base added: `CONTINUE.md` (always loaded) + `docs/STATE.md` (handoff) + `docs/wiki/*`
  (decisions, gotchas, eval, chunking). Linted by `scripts/lint_docs.py` in pre-commit.

## Next
1. `make check` passes (fix model names via the `SENTINEL_*` env vars)
2. Clone jaffle_shop_duckdb into `data/repos/` and write the 8 patches listed in `bugs/bugs.yaml`
3. M1: ingestion (dbt manifest + sqlglot chunker, one chunk per model)

## Open questions
- Does Ollama reranking work with the community reranker, or fall back to sentence-transformers? (decide in M3)

## How to run
`uv sync`, then `make check`, `make test`, `make lint`.

## Session protocol
- Start: read this file, then do the first item under Next.
- End: update this file (keep it under 40 lines), add new lessons to `docs/wiki/gotchas.md`,
  keep `## Status` in `README.md` in sync, and commit.
