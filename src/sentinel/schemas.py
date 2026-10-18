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


class Lineage(BaseModel):
    """Deterministic lineage for one model, derived from the dbt manifest.

    Upstream/downstream are model/seed names (not unique_ids) so they read well
    in findings. Tests are excluded -- they are edges dbt draws, not data flow.
    """

    upstream: list[str] = []
    downstream: list[str] = []


class Chunk(BaseModel):
    """One chunk per dbt model: enough for retrieval + M4 diffing."""

    model_name: str
    unique_id: str
    raw_code: str
    description: str = ""
    columns: dict[str, str] = Field(default_factory=dict)
    ctes: list[str] = []
    cte_columns: dict[str, list[str]] = Field(default_factory=dict)
    selects: list[str] = []
    parsed: bool = True
    parsed_error: str | None = None
    lineage: Lineage = Field(default_factory=Lineage)

    def search_text(self) -> str:
        """Flat text the vector/BM25 index embeds for this chunk."""
        lines = [
            f"model {self.model_name}",
            self.description,
            "columns: " + ", ".join(f"{c} ({d})" for c, d in self.columns.items()),
            "ctes: " + ", ".join(self.ctes) if self.ctes else "",
            "upstream: " + ", ".join(self.lineage.upstream) if self.lineage.upstream else "",
            "downstream: " + ", ".join(self.lineage.downstream) if self.lineage.downstream else "",
        ]
        return "\n".join(line for line in lines if line)

