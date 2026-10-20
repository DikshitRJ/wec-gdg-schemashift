"""Schema map contracts: frozen map, tables, columns, decisions.

Spec: foundation/schema-map
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SourceInfo(BaseModel, extra="forbid"):
    """Source database metadata."""

    kind: str = "mongodb"
    database: str = ""
    collections: list[str] = Field(default_factory=list)


class Column(BaseModel, extra="forbid"):
    """A target SQL column."""

    name: str
    pg_type: str
    nullable: bool = True
    identity: bool = False
    source_path: str = ""
    transform: str = "identity"
    on_error: str = "fail"
    default: str | None = None


class ForeignKey(BaseModel, extra="forbid"):
    """A foreign key constraint."""

    columns: list[str]
    ref_table: str
    ref_columns: list[str]
    on_delete: str = "NO ACTION"


class Index(BaseModel, extra="forbid"):
    """An index on one or more columns."""

    columns: list[str]
    unique: bool = False


class Table(BaseModel, extra="forbid"):
    """A target SQL table derived from one source collection/path."""

    name: str
    kind: str = "root"  # root | child
    origin_collection: str = ""
    origin_path: str = ""
    primary_key: list[str] = Field(default_factory=lambda: ["id"])
    columns: list[Column] = Field(default_factory=list)
    foreign_keys: list[ForeignKey] = Field(default_factory=list)
    indexes: list[Index] = Field(default_factory=list)


class Decision(BaseModel, extra="forbid"):
    """A recorded inference decision with evidence."""

    id: str
    rule: str
    choice: str
    alternatives: list[str] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)
    provenance: str = "rule"  # rule | llm_proposed_validated | override
    ambiguity: bool = False


class ApprovalRecord(BaseModel, extra="forbid"):
    """An approval entry for the gate ledger."""

    decision_id: str
    action: str  # approve | reject | edit
    approver: str = ""
    timestamp: str = ""
    reason: str = ""


class SchemaMap(BaseModel, extra="forbid"):
    """The frozen schema map — the single source of truth for all downstream layers."""

    map_version: int = 1
    map_hash: str = ""
    source: SourceInfo = SourceInfo()
    tables: list[Table] = Field(default_factory=list)
    decisions: list[Decision] = Field(default_factory=list)
