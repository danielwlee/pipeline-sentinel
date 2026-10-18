from pathlib import Path

import typer

from sentinel import ingest as ingest_mod

app = typer.Typer(help="Local agentic reviewer for dbt/SQL repos. No code leaves your machine.")


@app.command()
def ingest(
    repo: str = typer.Argument(..., help="Path to a dbt repo"),
    profiles_dir: str = typer.Option(None, help="dbt --profiles-dir (defaults to repo's ~/.dbt)"),
    index_dir: str = typer.Option(None, help="Where to write chunks/lineage (default: data/index)"),
):
    """M1: parse manifest + SQL, chunk per model, write chunks and lineage graph."""
    chunks, _lineage = ingest_mod.ingest(
        repo,
        index_dir=index_dir,
        profiles_dir=Path(profiles_dir) if profiles_dir else None,
    )
    typer.echo(f"Ingested {len(chunks)} model(s) into {index_dir or 'data/index'}.")
    for chunk in chunks:
        status = "OK" if chunk.parsed else f"PARSE-FAIL ({chunk.parsed_error})"
        typer.echo(
            f"  - {chunk.model_name}: {len(chunk.ctes)} CTE, "
            f"{len(chunk.selects)} cols, upstream={chunk.lineage.upstream}, "
            f"downstream={chunk.lineage.downstream} [{status}]"
        )


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

