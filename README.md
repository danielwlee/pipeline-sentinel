# pipeline-sentinel

Local, privacy-first agentic RAG reviewer for dbt / SQL repositories. Runs entirely on Ollama.

## Status
| Milestone | Status |
|---|---|
| M0 sanity check | in progress |
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

See [docs/architecture.md](docs/architecture.md). For session handoff read [docs/STATE.md](docs/STATE.md); notes live in [docs/wiki/](docs/wiki/README.md). Benchmarks will go here after M3/M6.
