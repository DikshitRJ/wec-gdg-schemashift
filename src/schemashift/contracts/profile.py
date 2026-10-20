"""Source profile contracts: collection/field statistics.

Spec: foundation/profile
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class FieldProfile(BaseModel, extra="forbid"):
    """Type and value statistics for a single document path."""

    path: str
    types: dict[str, int] = Field(default_factory=dict)  # bson_type -> count
    presence_rate: float = 1.0
    total_docs: int = 0
    string_lengths: dict[str, int | float] = Field(default_factory=dict)  # min, max, mean
    numeric_range: dict[str, float] = Field(default_factory=dict)  # min, max
    decimal_digits: int = 0
    distinct_estimate: int = 0
    array_lengths: dict[str, float] = Field(default_factory=dict)  # min, max, mean
    key_set_signatures: list[str] = Field(default_factory=list)
    key_variance: float = 0.0  # 0 = all same keys, 1 = all different
    examples: list[Any] = Field(default_factory=list, max_length=3)
    is_unique: bool = False
    is_array: bool = False
    is_object: bool = False


class CollectionProfile(BaseModel, extra="forbid"):
    """Profile of a single MongoDB collection."""

    name: str
    doc_count: int = 0
    sample_count: int = 0
    fields: list[FieldProfile] = Field(default_factory=list)


class SourceProfile(BaseModel, extra="forbid"):
    """Complete profile of the source MongoDB database."""

    database: str = ""
    collections: list[CollectionProfile] = Field(default_factory=list)
    sample_size: int = 0
