# CONTINUE.md — always loaded

Local, privacy-first agentic RAG reviewer for dbt/SQL repos (Ollama only).
**First:** read [docs/STATE.md](docs/STATE.md), then do its first "Next" item. **On demand:** [docs/wiki/README.md](docs/wiki/README.md).

## Rule
Deterministic tools compute lineage and diffs; the LLM only interprets and explains. Never guess lineage.

## Commands
- `uv sync` to install. Always run Python via `uv run`.
- `make check` verifies the Ollama models (M0); `make test` / `make lint` run pytest / ruff (line length 100).
- `uv run sentinel --help` lists: ingest, ask, diff, review.

## Layout
Code in `src/sentinel/` (config.py, schemas.py, cli.py). Ground truth: `bugs/bugs.yaml`,
`evals/golden_questions.yaml`. Runtime data: `data/` (gitignored).

## Conventions
- Config from env vars in `config.py` (SENTINEL_LLM, SENTINEL_EMBED, SENTINEL_RERANK, SENTINEL_NUM_CTX=32768).
- Agent output must validate against `Review` in `schemas.py`. `review` is dry-run; posting needs `--post` + approval.
- Local only: no cloud LLM calls, no telemetry.
- Conventional Commits; branches `<milestone>/<description>`. Never commit to `main` — branch off latest main, then PR.
- PRs need a milestone via `gh pr create --milestone "<Title>"` (title, not number; list with
  `gh api "repos/danielwlee/pipeline-sentinel/milestones"`).

## Session ritual
Start: read `docs/STATE.md`, then do X. End: update `docs/STATE.md`, add lessons to
`docs/wiki/gotchas.md`, keep `## Status` in `README.md` in sync, and commit. Review any wiki edits.
