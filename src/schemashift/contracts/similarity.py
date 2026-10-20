"""Similarity report contracts.

Spec: foundation/similarity-models
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class Band(StrEnum):
    """Confidence band for a mapping."""

    MATCHED = "matched"
    GUESSED = "guessed"
    NEEDS_REVIEW = "needs_review"


class FieldScore(BaseModel, extra="forbid"):
    """Score for a single source field → target column mapping."""

    source_path: str
    target_column: str = ""
    target_table: str = ""
    name_score: float = 0.0
    type_score: float = 0.0
    structure_score: float = 0.0
    constraint_score: float = 0.0
    total: float = 0.0
    band: Band = Band.NEEDS_REVIEW
    reason_codes: list[str] = Field(default_factory=list)
    capped: bool = False


class EntityScore(BaseModel, extra="forbid"):
    """Score for a single collection → table(s) mapping."""

    collection: str
    tables: list[str] = Field(default_factory=list)
    field_scores: list[FieldScore] = Field(default_factory=list)
    total: float = 0.0
    field_count: int = 0
    matched_count: int = 0
    guessed_count: int = 0
    needs_review_count: int = 0


class SimilarityReport(BaseModel, extra="forbid"):
    """Complete similarity report: overall, per-entity, per-field scores."""

    overall_score: float = 0.0
    overall_band: Band = Band.NEEDS_REVIEW
    entity_scores: list[EntityScore] = Field(default_factory=list)
    drag_list: list[FieldScore] = Field(default_factory=list)
    total_fields: int = 0
    matched_fields: int = 0
    guessed_fields: int = 0
    needs_review_fields: int = 0
