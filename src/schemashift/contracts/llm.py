"""LLM interaction contracts: proposals, explanations, patches.

Spec: foundation/llm-models
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ProposedDecision(BaseModel, extra="forbid"):
    """A single LLM-proposed schema decision."""

    target_path: str  # e.g. "orders.items" or "reviews.rating"
    suggestion: str  # e.g. "rename to order_line_items"
    category: str  # rename | strategy | type | relation
    confidence: float = 0.5
    rationale: str = ""


class SchemaProposal(BaseModel, extra="forbid"):
    """LLM proposals for schema naming/structure decisions."""

    proposals: list[ProposedDecision] = Field(default_factory=list)


class ExplanationNote(BaseModel, extra="forbid"):
    """LLM-generated explanation for similarity scores or drift."""

    section: str = ""
    text: str = ""
    ambiguous_pairs: list[dict[str, str]] = Field(default_factory=list)


class RemapPatch(BaseModel, extra="forbid"):
    """LLM-suggested remap to fix failed rows."""

    target: str = ""
    changes: dict[str, str] = Field(default_factory=dict)
    rationale: str = ""


class ScriptAnnotation(BaseModel, extra="forbid"):
    """LLM-generated annotation for migration scripts."""

    risk_level: str = "low"  # low | medium | high
    notes: list[str] = Field(default_factory=list)
    summary: str = ""


class RefactorNote(BaseModel, extra="forbid"):
    """LLM-suggested refactoring for the ORM layer."""

    file: str = ""
    location: str = ""
    suggestion: str = ""
    rationale: str = ""
