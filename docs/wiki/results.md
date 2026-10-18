# Results

Short log of what the test suites / seeded bugs exercise, and how to run them.
Keep entries brief; this is a running summary, not a transcript.

## M1 ingestion — verification done

Pipeline is deterministic and LLM-free; verified end-to-end on `jaffle_shop_duckdb`.

- **Ingestion**: `dbt parse` (no DB connection) -> `chunker.parse_structure` (jinja-stripped
  sqlglot, one chunk per model) -> `data/index/chunks/*.json` + `lineage.json`.
  All 5 models parse to correct chunks + lineage.
- **Unit**: `uv run pytest` -- `tests/test_smoke.py` validates the `Review`/`Finding`/`Severity`
  schema contract the agent must emit.
- **Lint**: `uv run ruff check src tests` clean; `scripts/lint_docs.py` ("knowledge base OK")
  enforces wiki page-size caps.

## M4 seeded breaking changes (ground truth: `bugs/bugs.yaml`)

Eight hand-written git-diff patches against a clean `jaffle_shop_duckdb`, each seeded to trip a
specific detector. They are the **fixtures** for the deterministic breaking-change detector
(`diff` command); the M4 work is the detector that *reads* them. Severity is the expected call.

| id | model | category | expected | what it does |
|----|-------|----------|----------|--------------|
| 01 | stg_customers | dropped_column | breaking | drops `customer_id` from the select |
| 02 | stg_orders | renamed_column | breaking | `status` -> `order_status`, no downstream update |
| 03 | stg_payments | type_change | risky | `cast(amount/100 as integer)` -- precision loss |
| 04 | orders | grain_change | breaking | join payments without aggregating -> dup rows |
| 05 | customers | lineage_change | risky | `ref('stg_orders')` -> hardcoded `raw_orders` |
| 06 | orders | test_removed | minor | delete `unique` test on `order_id` (schema.yml) |
| 07 | stg_customers | lint | minor | introduce `select *` (convention violation) |
| 08 | customers | none | info | comment-only; negative control, must NOT flag |

Run / inspect: each `bugs/NN_*.patch` is a `git diff` of the change; `bugs/bugs.yaml` is the
authoritative catalog (id, model, category, expected_severity, note). Patches are currently
untracked (M1 close-out left them for "Next item 2").
