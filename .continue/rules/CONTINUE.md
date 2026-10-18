---
description: pipeline-sentinel, local agentic RAG reviewer for dbt/SQL repos (Ollama only)
---
# pipeline-sentinel

Local, privacy-first CLI. Reviews dbt/SQL diffs using hybrid retrieval (LanceDB BM25 + vectors + rerank), a deterministic lineage/schema diff (sqlglot + dbt manifest), a LangGraph agent, a structured Pydantic review, and dry-run PR comments via `gh`.

**Rule:** deterministic tools compute lineage and diffs; the LLM only interprets and explains. Never guess lineage.

## Commands
- `uv sync` to install. Always run Python via `uv run`.
- `make check` verifies the Ollama models (M0)
- `make test` / `make lint` run pytest / ruff (line length 100)
- `uv run sentinel --help` lists the commands: ingest, ask, diff, review

## Layout
Code is in `src/sentinel/` (config.py, schemas.py, cli.py). Ground truth is in `bugs/bugs.yaml` and `evals/golden_questions.yaml`. Runtime data goes in `data/` (gitignored).

## Conventions
- All config comes from env vars read in `config.py` (SENTINEL_LLM, SENTINEL_EMBED, SENTINEL_RERANK, SENTINEL_NUM_CTX=32768)
- Agent output must validate against `Review` in `schemas.py`
- `review` is dry-run by default; posting needs `--post` plus approval
- Local only: never add cloud LLM calls or telemetry
- Conventional Commits; branches named `<milestone>/<description>`

## Tools
Run shell commands only with `run_terminal_command`. Do not invent tool names.