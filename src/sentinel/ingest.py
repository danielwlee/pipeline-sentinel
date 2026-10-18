"""M1 ingestion: manifest + SQL -> one Chunk per model + lineage graph.

Pipeline:
  1. dbt parse  -> target/manifest.json   (no DB connection)
  2. extract_dependencies / extract_downstream   (deterministic lineage)
  3. per model: parse_structure + assemble a Chunk
  4. write chunks/*.json  +  lineage.json  +  manifest symlink

The LLM is NOT involved here -- ingestion is 100% deterministic so M4 diffing and
M3 retrieval both start from a reproducible, side-effect-free artifact.
"""
from __future__ import annotations

import json
from pathlib import Path

from sentinel import chunker, manifest
from sentinel.config import INDEX_DIR
from sentinel.schemas import Chunk, Lineage


def _column_map(model):
    """model.columns -> {col_name: description}. Empty for seed-backed models."""
    out = {}
    for name, meta in (model.get("columns", {}) or {}).items():
        out[name] = (meta or {}).get("description", "")
    return out


def _resolve_names(manifest_data, uids):
    """unique_ids -> sorted, de-duplicated human names."""
    return sorted({manifest.resolve_name(manifest_data, uid) for uid in uids})


def build_chunk(model, manifest_data):
    """Assemble a Chunk for a single model node from the manifest."""
    uid = model["unique_id"]
    structure = chunker.parse_structure(model.get("raw_code", ""))
    lineage = Lineage(
        upstream=_resolve_names(manifest_data, manifest.extract_dependencies(manifest_data).get(uid, [])),
        downstream=_resolve_names(manifest_data, manifest.extract_downstream(manifest_data).get(uid, [])),
    )
    return Chunk(
        model_name=model.get("name", uid.split(".")[-1]),
        unique_id=uid,
        raw_code=model.get("raw_code", ""),
        description=model.get("description", ""),
        columns=_column_map(model),
        ctes=structure["ctes"],
        selects=structure["selects"],
        parsed=structure["parsed"],
        parsed_error=structure["error"],
        lineage=lineage,
    )


def build_lineage(manifest_data):
    """manifest_data -> {model_name: Lineage} across every model + seed node."""
    deps = manifest.extract_dependencies(manifest_data)
    down = manifest.extract_downstream(manifest_data)
    out = {}
    for uid in sorted(set(deps) | set(down)):
        name = manifest.resolve_name(manifest_data, uid)
        out[name] = Lineage(
            upstream=_resolve_names(manifest_data, deps.get(uid, [])),
            downstream=_resolve_names(manifest_data, down.get(uid, [])),
        )
    return out


def _link_manifest(index_dir, manifest_path):
    """Point index_dir/manifest.json at the parsed manifest, idempotently."""
    link = index_dir / "manifest.json"
    target = Path(manifest_path).resolve()
    if link.is_symlink() or link.exists():
        link.unlink()
    link.symlink_to(target, target_is_directory=False)


def _dump(obj):
    """Serialize a Chunk/Lineage (or dict of them) to a JSON string."""
    if isinstance(obj, Chunk):
        obj = obj.model_dump()
    elif isinstance(obj, dict):
        obj = {k: (v.model_dump() if isinstance(v, Lineage) else v) for k, v in obj.items()}
    return json.dumps(obj, indent=2)


def ingest(repo, index_dir=None, profiles_dir=None):
    """Run the full ingestion and return (chunks, lineage)."""
    repo = Path(repo).resolve()
    index_dir = Path(index_dir or INDEX_DIR)
    manifest_path = manifest.run_dbt_parse(repo, profiles_dir=profiles_dir)
    data = manifest.load_manifest(manifest_path)

    chunks = [build_chunk(m, data) for m in manifest.get_models(data)]
    lineage = build_lineage(data)

    out_dir = index_dir / "chunks"
    out_dir.mkdir(parents=True, exist_ok=True)
    for chunk in chunks:
        (out_dir / f"{chunk.model_name}.json").write_text(_dump(chunk))
    (index_dir / "lineage.json").write_text(_dump(lineage))
    _link_manifest(index_dir, manifest_path)
    return chunks, lineage
