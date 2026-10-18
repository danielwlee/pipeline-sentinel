#!/usr/bin/env bash
# Scaffolds the pipeline-sentinel repo. Usage: bash bootstrap.sh [target-dir]
set -euo pipefail
ROOT="${1:-pipeline-sentinel}"
mkdir -p "$ROOT"/{src/sentinel,tests,scripts,docs,evals,bugs,.github/workflows,data}
cd "$ROOT"

cat > .gitignore <<'EOF'
.venv/
__pycache__/
.lancedb/
data/repos/
data/index/
*.egg-info/
.env
.pytest_cache/
.ruff_cache/
EOF

cat > pyproject.toml <<'EOF'
[project]
name = "pipeline-sentinel"
version = "0.1.0"
description = "Local agentic RAG reviewer for dbt/SQL pipeline repos (Ollama only)"
requires-python = ">=3.11"
dependencies = [
  "typer>=0.12",
  "rich>=13",
  "pydantic>=2.7",
  "pyyaml>=6",
  "ollama>=0.3",
  "lancedb>=0.13",
  "sqlglot>=25",
  "sqlfluff>=3",
  "langgraph>=0.2",
  "dbt-core>=1.8",
  "dbt-duckdb>=1.8",
]

[dependency-groups]
dev = ["pytest>=8", "ruff>=0.6"]

[project.scripts]
sentinel = "sentinel.cli:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/sentinel"]

[tool.ruff]
line-length = 100
EOF

cat > Makefile <<'EOF'
.PHONY: setup check test lint
setup:
	uv sync
check:
	uv run python scripts/m0_check.py
test:
	uv run pytest -q
lint:
	uv run ruff check src tests
EOF

cat > src/sentinel/__init__.py <<'EOF'
__version__ = "0.1.0"
EOF

cat > src/sentinel/config.py <<'EOF'
"""Central config. Override any model via env var; verify names with `ollama list`."""
import os

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
LLM_MODEL = os.getenv("SENTINEL_LLM", "qwen3.8:27b-mlx")
EMBED_MODEL = os.getenv("SENTINEL_EMBED", "embeddinggemma-2:740m")
RERANK_MODEL = os.getenv("SENTINEL_RERANK", "pdurugyan/qwen3-reranker-0.6b-q8_0:latest")
# 32k is plenty for the agent; 128k costs lots of KV-cache memory and speed.
NUM_CTX = int(os.getenv("SENTINEL_NUM_CTX", "32768"))
INDEX_DIR = os.getenv("SENTINEL_INDEX_DIR", "data/index")
EOF

cat > src/sentinel/schemas.py <<'EOF'
"""Structured output contracts (Pydantic). The agent must emit a Review."""
from enum import Enum

from pydantic import BaseModel, Field


class Severity(str, Enum):
    breaking = "breaking"
    risky = "risky"
    minor = "minor"
    info = "info"


class Finding(BaseModel):
    model_name: str
    severity: Severity
    category: str = Field(description="e.g. dropped_column, type_change, grain_change, lint")
    evidence: str = Field(description="Deterministic tool output backing the claim")
    affected_downstream: list[str] = []
    suggestion: str = ""


class Review(BaseModel):
    summary: str
    findings: list[Finding]
    approve: bool
EOF

cat > src/sentinel/cli.py <<'EOF'
import typer

app = typer.Typer(help="Local agentic reviewer for dbt/SQL repos. No code leaves your machine.")


@app.command()
def ingest(repo: str = typer.Argument(..., help="Path to a dbt repo")):
    """M1: parse manifest + SQL, chunk per model, write chunks and lineage graph."""
    raise NotImplementedError("Milestone M1")


@app.command()
def ask(question: str):
    """M2/M3: retrieval-augmented Q&A over the ingested repo."""
    raise NotImplementedError("Milestone M2")


@app.command()
def diff(base: str = "main", head: str = "HEAD"):
    """M4: deterministic breaking-change detection (no LLM)."""
    raise NotImplementedError("Milestone M4")


@app.command()
def review(pr: int = typer.Option(None), post: bool = typer.Option(False, help="Post to GitHub")):
    """M5/M6: agentic review. Dry-run unless --post is given and approved."""
    raise NotImplementedError("Milestone M5")


if __name__ == "__main__":
    app()
EOF

cat > scripts/m0_check.py <<'EOF'
"""M0 sanity check: are models pulled, and how fast is the LLM at 32k context?"""
import json
import sys
import time
import urllib.request

sys.path.insert(0, "src")
from sentinel import config  # noqa: E402


def call(path, payload=None):
    req = urllib.request.Request(
        config.OLLAMA_HOST + path,
        data=json.dumps(payload).encode() if payload else None,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.load(r)


def main():
    try:
        have = {m["name"] for m in call("/api/tags")["models"]}
    except Exception as e:
        sys.exit(f"Ollama not reachable at {config.OLLAMA_HOST}: {e}")
    ok = True
    for label, name in [("LLM", config.LLM_MODEL), ("embed", config.EMBED_MODEL),
                        ("rerank", config.RERANK_MODEL)]:
        found = name in have or f"{name}:latest" in have
        ok &= found
        print(f"[{'ok' if found else 'MISSING'}] {label}: {name}")
    if not ok:
        print("\nAvailable:", *sorted(have), sep="\n  ")
        sys.exit("Fix names (env vars SENTINEL_LLM / SENTINEL_EMBED / SENTINEL_RERANK).")
    t = time.time()
    r = call("/api/chat", {"model": config.LLM_MODEL, "stream": False,
             "messages": [{"role": "user", "content": "Reply with the word: ready"}],
             "options": {"num_ctx": config.NUM_CTX}})
    print(f"LLM reply in {time.time()-t:.1f}s: {r['message']['content'][:80]!r}")
    e = call("/api/embed", {"model": config.EMBED_MODEL, "input": "select 1"})
    print(f"Embedding dim: {len(e['embeddings'][0])}")


if __name__ == "__main__":
    main()
EOF

cat > tests/test_smoke.py <<'EOF'
from sentinel.schemas import Finding, Review, Severity


def test_review_schema():
    f = Finding(model_name="stg_customers", severity=Severity.breaking,
                category="dropped_column", evidence="column customer_id removed")
    assert Review(summary="x", findings=[f], approve=False).findings[0].severity == "breaking"
EOF

cat > bugs/bugs.yaml <<'EOF'
# Seeded breaking changes for jaffle_shop_duckdb. Ground truth for M4/M6 evals.
# Implement each as a patch file bugs/NN_name.patch (git diff against the clean repo).
bugs:
  - id: 01_drop_column
    model: stg_customers
    category: dropped_column
    expected_severity: breaking
    note: remove customer_id from select; downstream customers/orders join on it
  - id: 02_rename_column
    model: stg_orders
    category: renamed_column
    expected_severity: breaking
    note: rename status -> order_status without updating downstream
  - id: 03_type_change
    model: stg_payments
    category: type_change
    expected_severity: risky
    note: cast amount to integer (precision loss)
  - id: 04_grain_change
    model: orders
    category: grain_change
    expected_severity: breaking
    note: join payments without aggregating -> duplicate order rows
  - id: 05_remove_ref
    model: customers
    category: lineage_change
    expected_severity: risky
    note: replace ref('orders') with hardcoded schema.table
  - id: 06_remove_test
    model: orders
    category: test_removed
    expected_severity: minor
    note: delete unique test on order_id in schema.yml
  - id: 07_select_star
    model: stg_customers
    category: lint
    expected_severity: minor
    note: introduce select * (convention violation)
  - id: 08_benign
    model: customers
    category: none
    expected_severity: info
    note: negative control, comment-only change; must NOT be flagged
EOF

cat > evals/golden_questions.yaml <<'EOF'
# M3 golden set: ~30 questions with the model(s) that should be retrieved.
questions:
  - q: Which models use customer_id?
    relevant: [stg_customers, customers, orders]
  - q: Where are payment amounts converted from cents?
    relevant: [stg_payments]
EOF

cat > docs/architecture.md <<'EOF'
# Architecture

```mermaid
flowchart LR
  A[Git diff / PR] --> B[Agent: LangGraph + Ollama]
  B --> C[Tool: hybrid search]
  B --> D[Tool: lineage and schema diff]
  B --> E[Tool: sqlfluff lint]
  B --> F[Tool: read_file]
  C --> G[(LanceDB: vectors + BM25)]
  G --> H[Reranker]
  I[Ingest: dbt manifest + sqlglot chunker] --> G
  D --> J[dbt manifest.json + sqlglot]
  B --> K[Structured review: Pydantic]
  K --> L[Human approval] --> M[gh CLI: PR comment]
  B -.traces.-> N[Phoenix, self-hosted]
```

Principle: deterministic tools compute lineage; the LLM interprets and explains.
EOF

cat > README.md <<'EOF'
# pipeline-sentinel

Local, privacy-first agentic RAG reviewer for dbt / SQL repositories. Runs entirely on Ollama.

## Status
| Milestone | Status |
|---|---|
| M0 sanity check | todo |
| M1 ingestion | todo |
| M2 vector RAG | todo |
| M3 hybrid + rerank + eval | todo |
| M4 breaking-change detector | todo |
| M5 agent | todo |
| M6 GitHub + evals | todo |

## Quickstart
```bash
uv sync
make check        # verifies Ollama models
uv run sentinel --help
```

See [docs/architecture.md](docs/architecture.md). Benchmarks will go here after M3/M6.
EOF

cat > .github/workflows/ci.yml <<'EOF'
name: ci
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv sync
      - run: uv run ruff check src tests
      - run: uv run pytest -q
EOF

git init -q 2>/dev/null || true
echo "Scaffolded in $(pwd)"
echo "Next: cd $ROOT && uv sync && ollama list && make check"
echo "Then: git clone https://github.com/dbt-labs/jaffle_shop_duckdb data/repos/jaffle_shop_duckdb"
