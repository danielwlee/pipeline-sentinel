"""dbt manifest loading + deterministic lineage extraction.

Design rule (docs/architecture.md): deterministic tools compute lineage; the LLM
only interprets and explains. We therefore read lineage straight from the dbt
manifest -- the authoritative graph dbt itself builds -- rather than asking the
LLM or re-deriving it by string-matching.

The manifest is produced by `dbt parse`, which needs NO database connection
(it only reads the project files + profiles). This keeps ingestion 100% local
and side-effect-free: no `.duckdb` file is opened.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path


def run_dbt_parse(repo, profiles_dir=None, project_dir=None):
    """Run `dbt parse` in *repo* and return the path to the produced manifest.

    `dbt parse` builds `target/manifest.json` without opening a database, so this
    is safe to call on a clean checkout. The manifest is the single source of
    truth for node metadata + lineage.

    Paths are resolved to absolute before the subprocess runs, because dbt is
    invoked with cwd=repo and a relative --project-dir would not resolve there.
    """
    repo = Path(repo).resolve()
    cmd = ["dbt", "parse", "--project-dir", str((project_dir or repo).resolve())]
    if profiles_dir is not None:
        cmd += ["--profiles-dir", str(Path(profiles_dir).resolve())]
    subprocess.run(cmd, cwd=repo, check=True)
    manifest = repo / "target" / "manifest.json"
    if not manifest.exists():
        raise RuntimeError(f"dbt parse did not produce {manifest}")
    return manifest


def load_manifest(manifest_path):
    """Load and minimally validate a dbt manifest.json."""
    with open(manifest_path) as fh:
        data = json.load(fh)
    if "nodes" not in data:
        raise ValueError("not a dbt manifest: missing 'nodes' key")
    return data


def _node_name(node):
    return node.get("name", node.get("unique_id", ""))


def _valid_data_nodes(manifest):
    nodes = manifest.get("nodes", {})
    return {uid for uid, n in nodes.items() if n.get("resource_type") in ("model", "seed")}


def extract_dependencies(manifest):
    """model_id -> sorted parent ids (restricted to model/seed nodes).

    Tests are excluded so the lineage graph shows real data flow, not test edges.
    """
    valid = _valid_data_nodes(manifest)
    depends_on = {}
    for uid, parents in manifest.get("parent_map", {}).items():
        pars = sorted(p for p in parents if p in valid and p != uid)
        if uid in valid:
            depends_on[uid] = pars
    return depends_on


def extract_downstream(manifest):
    """model_id -> sorted child ids (restricted to model/seed nodes)."""
    valid = _valid_data_nodes(manifest)
    downstream = {}
    for uid, children in manifest.get("child_map", {}).items():
        kids = sorted(c for c in children if c in valid and c != uid)
        if uid in valid:
            downstream[uid] = kids
    return downstream


def get_models(manifest):
    """Return model nodes only, sorted by name for stable output."""
    models = [n for n in manifest.get("nodes", {}).values() if n.get("resource_type") == "model"]
    return sorted(models, key=lambda n: n.get("name", ""))


def get_seeds(manifest):
    """Return seed nodes keyed by unique_id (used to resolve seed names)."""
    return {
        uid: n
        for uid, n in manifest.get("nodes", {}).items()
        if n.get("resource_type") == "seed"
    }


def resolve_name(manifest, uid):
    """Resolve a manifest unique_id to a human name (model/seed/test name)."""
    node = manifest.get("nodes", {}).get(uid) or manifest.get("sources", {}).get(uid)
    return _node_name(node) if node else uid.split(".")[-1]
