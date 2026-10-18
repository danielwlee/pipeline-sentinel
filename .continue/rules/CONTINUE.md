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
- **Always create a new branch before opening a PR** — never commit to `main` directly. Create a fresh `<milestone>/<description>` branch off the latest `main`, commit there, and open the PR from it.
- Every PR I open must be assigned to the matching GitHub milestone via `gh pr create --milestone`. Map the work to the right milestone from context (scaffold/setup → M0, ingestion → M1, vector RAG → M2, hybrid/rerank/eval → M3, breaking-change detector → M4, agent → M5, GitHub integration/eval/polish → M6, MCP server → its own milestone). Pass the milestone **title** to `--milestone` (verified: `gh` resolves milestones by title, not number; passing the number fails with "not found"), e.g. `--milestone "M0: Sanity check"`; re-list milestones with `gh api "repos/danielwlee/pipeline-sentinel/milestones"` before opening a PR in case new ones were added.

## Tools
- Run shell commands only with `run_terminal_command`. Do not invent tool names.
- Edit existing files with only `edit_existing_file`.

## Failure protocol
- If a tool call or command fails twice, stop. Do not try a third time.
- Reply with: what failed, the exact error, and your best guess at the cause. Wait for me.
- After I confirm a fix, add one line to docs/wiki/gotchas.md in the form: symptom -> cause -> fix
- Before retrying anything similar, check docs/wiki/gotchas.md.

## File edits
- Never write or change files with the shell (no heredocs, `cat >`, `sed -i`, `echo >`).
- Use create_new_file for new files and edit_existing_file for changes, in small targeted edits.
- Use run_terminal_command only to run things (uv run, pytest, git status).
- edit_existing_file takes filepath and changes. `changes` is only the modified code, with `# ... existing code ...` for unchanged parts. No old/new strings, no code fences. Read the file first. One call at a time.
- If edit_existing_file fails twice, stop and ask me. Do not fall back to the shell.
- Read files with read_file, not cat. Read each file once, only the part you need. Don't chain commands with &&.