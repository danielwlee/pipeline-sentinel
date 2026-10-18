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
