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
