---
description: Comprehensive project guide for pipeline-sentinel, a local agentic RAG reviewer for dbt/SQL repos.
---

# Pipeline Sentinel — Project Guide

## 1. Project Overview

**pipeline-sentinel** is a local, privacy-first agentic RAG (Retrieval-Augmented Generation) reviewer for dbt/SQL data pipeline repositories. It takes a git diff from a dbt/Airflow/SQL repo, retrieves relevant context via hybrid search, checks for breaking schema and lineage changes, and drafts a structured PR review. Everything runs locally on **Ollama** — no code or data leaves the machine.

### Key Technologies

| Technology | Role |
|---|---|
| **Python ≥3.11** | Implementation language |
| **Typer** | CLI framework |
| **Pydantic v2** | Structured output contracts (`Finding`, `Review`, `Severity`) |
| **Ollama** | Local LLM inference (LLM, embeddings, reranker) |
| **LanceDB** | Vector + BM25 hybrid index storage |
| **sqlglot** | SQL parsing and lineage extraction |
| **sqlfluff** | SQL linting |
| **LangGraph** | Agent orchestration (state machine) |
| **dbt-core + dbt-duckdb** | dbt manifest parsing, DuckDB adapter |
| **Rich** | Terminal UI formatting |
| **uv** | Fast Python package manager / environment manager |

### High-Level Architecture

```
Git diff / PR
  → Agent (LangGraph + Ollama)
    → Tool: hybrid search (LanceDB: vectors + BM25 → Reranker)
    → Tool: lineage & schema diff (dbt manifest.json + sqlglot)
    → Tool: sqlfluff lint
    → Tool: read_file
  → Structured review (Pydantic)
  → Human approval
  → gh CLI: PR comment
  → Traces → Phoenix (self-hosted, optional)
```

**Principle:** Deterministic tools compute lineage and diffs; the LLM interprets and explains.

---

## 2. Getting Started

### Prerequisites

- **Python ≥ 3.11**
- **[uv](https://github.com/astral-sh/uv)** — fast Python package manager
- **Ollama** — local LLM runtime, running on `localhost:11434`
- **Ollama models** (verify with `ollama list`):
  - `SENTINEL_LLM` — `qwen3.8:27b-mlx` (default)
  - `SENTINEL_EMBED` — `embeddinggemma-2:740m`
  - `SENTINEL_RERANK` — `pdurugyan/qwen3-reranker-0.6b-q8_0:latest`
- **DuckDB** — pulled in via `dbt-duckdb`
- **Git** — for diff operations
- **GitHub CLI (`gh`)** — for posting PR comments (M5/M6)

### Installation

```bash
uv sync
uv run sentinel --help
```

### Verify Ollama Models (M0)

```bash
make check
# or:
uv run python scripts/m0_check.py
```

This checks that all three Ollama models are available and measures LLM latency at the configured context window.

### Basic Usage (stubs, not yet implemented)

```bash
uv run sentinel ingest /path/to/dbt/repo   # M1: parse manifest + SQL, chunk, index
uv run sentinel ask "Which models use customer_id?"  # M2/M3: RAG Q&A
uv run sentinel diff main HEAD             # M4: deterministic breaking-change detection
uv run sentinel review --pr 123           # M5/M6: agentic review (dry-run)
uv run sentinel review --pr 123 --post    # M5/M6: post review to GitHub
```

### Running Tests

```bash
make test
# or:
uv run pytest -q
```

---

## 3. Project Structure

```
pipeline-sentinel/
├── src/sentinel/          # Main Python package
│   ├── __init__.py        # Package version ("0.1.0")
│   ├── config.py          # Central config (env-var overrides for Ollama models, context, index dir)
│   ├── schemas.py         # Pydantic contracts: Severity enum, Finding, Review
│   └── cli.py             # Typer CLI entry point (stubs for M1–M6)
├── scripts/
│   └── m0_check.py        # M0 sanity check: verifies Ollama models are pulled + measures latency
├── tests/
│   └── test_smoke.py      # Smoke test for schema contracts
├── bugs/
│   └── bugs.yaml          # Seeded breaking-change cases (ground truth for M4/M6 evals)
├── evals/
│   └── golden_questions.yaml  # M3 golden eval set (~30 questions with expected retrieval)
├── docs/
│   └── architecture.md    # Mermaid diagram + design principles
├── data/                  # Runtime data (gitignored)
│   ├── repos/             # Cloned dbt repos (e.g. jaffle_shop_duckdb)
│   ├── index/             # LanceDB vector/BM25 index
│   └── (other runtime artifacts)
├── .github/workflows/
│   └── ci.yml             # GitHub Actions: ruff lint + pytest
├── .gitignore             # Ignores .venv, __pycache__, .lancedb, data/repos, data/index, .env
├── pyproject.toml         # Project metadata, dependencies, ruff config, hatchling build
├── Makefile               # setup / check / test / lint targets
├── bootstrap.sh           # Scaffold script (run once to create the repo structure)
└── README.md              # Project overview + status table
```

### Key Files

| File | Purpose |
|---|---|
| `src/sentinel/config.py` | All configuration; every value is overridable via environment variable |
| `src/sentinel/schemas.py` | The contract every agent output must conform to |
| `src/sentinel/cli.py` | Entry point; each CLI command maps to a milestone |
| `bugs/bugs.yaml` | Ground-truth test cases for evaluating detection accuracy |
| `evals/golden_questions.yaml` | Golden questions for retrieval quality (M3 eval) |
| `scripts/m0_check.py` | Prerequisite verification (Ollama connectivity + model availability) |

### Important Configuration

All config lives in `src/sentinel/config.py` and is overridden via environment variables:

| Env Var | Default | Purpose |
|---|---|---|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server address |
| `SENTINEL_LLM` | `qwen3.8:27b-mlx` | LLM model name |
| `SENTINEL_EMBED` | `embeddinggemma-2:740m` | Embedding model name |
| `SENTINEL_RERANK` | `pdurugyan/qwen3-reranker-0.6b-q8_0:latest` | Reranker model name |
| `SENTINEL_NUM_CTX` | `32768` | Context window size (32k) |
| `SENTINEL_INDEX_DIR` | `data/index` | Where LanceDB index lives |

---

## 4. Development Workflow

### Coding Standards

- **Linting:** `ruff` with `line-length = 100` (configured in `pyproject.toml` under `[tool.ruff]`)
- **Type hints:** Use Pydantic models for structured data; prefer type annotations throughout
- **Python version:** ≥3.11

### Testing Approach

- **Unit tests:** `pytest` in `tests/`
- **Smoke tests:** Verify schema contracts (`test_smoke.py`)
- **Eval tests:** Golden questions (`evals/golden_questions.yaml`) measure retrieval quality
- **Bug detection evals:** Seeded bugs (`bugs/bugs.yaml`) with expected severities; each bug has a patch file `bugs/NN_name.patch` (to be created)
- **CI:** GitHub Actions runs `ruff check` + `pytest` on every push/PR

### Build & Deployment

- **Build system:** `hatchling` (via `pyproject.toml`)
- **Package manager:** `uv`
- **Local dev:** `uv sync` installs everything; `uv run` executes in the virtualenv
- **No external deployment** — the tool runs locally. "Deployment" means installing on a developer machine or CI runner.

### Contribution Guidelines

1. Create a feature branch: `git checkout -b <milestone>/<description>`
2. Implement, run `make test && make lint`
3. Push and open a PR
4. CI must pass (ruff + pytest)

### Milestones

| Milestone | Status | Description |
|---|---|---|
| M0 | Todo | Sanity check: verify Ollama models are available |
| M1 | Todo | Ingestion: parse dbt manifest + SQL, chunk per model, write to LanceDB |
| M2 | Todo | Vector RAG: basic retrieval-augmented Q&A |
| M3 | Todo | Hybrid search + reranking + eval harness |
| M4 | Todo | Deterministic breaking-change detector (no LLM) |
| M5 | Todo | Agent orchestration via LangGraph |
| M6 | Todo | GitHub PR posting + full eval suite |

---

## 5. Key Concepts

### Domain-Specific Terminology

| Term | Meaning |
|---|---|
| **dbt model** | A SQL file in a dbt project that produces a table/view; has upstream/downstream lineage |
| **Breaking change** | A modification that would cause downstream models to fail or produce wrong results (e.g., dropping a column used in a JOIN) |
| **Grain change** | Change in the number of rows per entity (e.g., joining without aggregation causes duplicate rows) |
| **Lineage** | The dependency graph between dbt models (who depends on whom) |
| **Hybrid search** | Combining dense vector search (semantic) with sparse BM25 (keyword) for better retrieval |
| **Reranker** | A model that re-scores retrieved chunks to improve precision before passing to the LLM |
| **Finding** | A single issue detected in a review (severity, category, evidence, affected downstream) |
| **Review** | A complete review document: summary + list of findings + approve flag |
| **Golden question** | A test question with known relevant models; used to evaluate retrieval quality |

### Core Abstractions

- **`Finding`** (Pydantic): `model_name`, `severity` (breaking/risky/minor/info), `category`, `evidence`, `affected_downstream[]`, `suggestion`
- **`Review`** (Pydantic): `summary`, `findings[]`, `approve: bool`
- **`Severity`** (Enum): `breaking` > `risky` > `minor` > `info`

### Design Patterns

- **Tool-augmented agent:** The LLM (via LangGraph) calls deterministic tools; tools compute, LLM interprets
- **Structured output:** All agent output is validated via Pydantic schemas — the agent must emit a `Review`
- **Human-in-the-loop:** Reviews are dry-run by default; `--post` flag required to post to GitHub
- **Eval-driven development:** Golden questions and seeded bugs provide regression tests for detection quality

---

## 6. Common Tasks

### Run the M0 sanity check
```bash
make check
```

### Run tests
```bash
make test
```

### Run linter
```bash
make lint
# or individually:
uv run ruff check src tests
```

### Set up a new environment
```bash
uv sync
```

### Test with a dbt repo
```bash
git clone https://github.com/dbt-labs/jaffle_shop_duckdb data/repos/jaffle_shop_duckdb
uv run sentinel ingest data/repos/jaffle_shop_duckdb
```

### Change the LLM model
```bash
export SENTINEL_LLM="llama3.1:8b"
uv run python scripts/m0_check.py  # verify it works
```

### Create a bug patch (for eval)
```bash
# In a clean clone of jaffle_shop_duckdb:
# 1. Make the change described in bugs/bugs.yaml
# 2. Save as a git diff:
git diff > bugs/01_drop_column.patch
```

---

## 7. Troubleshooting

| Problem | Solution |
|---|---|
| `Ollama not reachable` | Start Ollama: `ollama serve`. Verify with `curl http://localhost:11434/api/tags` |
| Model not found in M0 check | Run `ollama pull <model-name>`. Check exact names with `ollama list` |
| Wrong model names | Override via env vars: `SENTINEL_LLM`, `SENTINEL_EMBED`, `SENTINEL_RERANK` |
| `uv: command not found` | Install uv: `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| `ImportError: sentinel` | Run `uv sync` first, then use `uv run` (not bare `python`) |
| High LLM latency | Reduce `SENTINEL_NUM_CTX` (default 32k). 128k costs significant KV-cache memory and speed |
| LanceDB index not found | Re-run `sentinel ingest` to rebuild the index |
| `sentinel review` does nothing | Commands are stubs (M1–M6 not implemented yet). Only M0 check works. |
| CI fails on ruff | Run `uv run ruff check --fix src tests` locally before pushing |
| `.git 2` folder created | Delete it: `rm -rf ".git 2"`. It's a side effect of `bootstrap.sh` running `git init` in an already-initialized repo |
| Missing `data/` subdirs | Run `mkdir -p data/repos data/index` or re-run `bootstrap.sh` |

### Debugging Tips

- Set `SENTINEL_NUM_CTX=4096` to debug faster (smaller context = faster inference)
- Check Ollama logs: `ollama logs` or the system log
- For LangGraph agent debugging, traces go to **Phoenix** (self-hosted) — see architecture doc
- Run `uv run python -c "from sentinel import config; print(config.LLM_MODEL)"` to verify config loading

---

## 8. References

### Internal
- `docs/architecture.md` — Full architecture diagram and design principles
- `bugs/bugs.yaml` — Ground-truth bug catalog with expected severities
- `evals/golden_questions.yaml` — Retrieval eval questions
- `README.md` — Project overview and status

### External

| Resource | URL |
|---|---|
| Ollama | https://ollama.com |
| LangGraph | https://langchain-ai.github.io/langgraph/ |
| LanceDB | https://lancedb.github.io/lancedb/ |
| sqlglot | https://sqlglot.com |
| sqlfluff | https://docs.sqlfluff.com |
| dbt | https://docs.getdbt.com |
| Typer | https://typer.tiangolo.com |
| Pydantic v2 | https://docs.pydantic.dev/latest/ |
| uv | https://docs.astral.sh/uv/ |
| jaffle_shop_duckdb | https://github.com/dbt-labs/jaffle_shop_duckdb |

### Model Verification
Always verify model names with:
```bash
ollama list
```
Model names in `config.py` are defaults and may need updating if Ollama releases new versions or renames models.