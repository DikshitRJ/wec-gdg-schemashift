"""Pydantic contracts re-exports.

Spec: foundation/contracts-init
"""

from schemashift.contracts.llm import (
    ExplanationNote,
    ProposedDecision,
    RemapPatch,
    SchemaProposal,
)
from schemashift.contracts.profile import (
    CollectionProfile,
    FieldProfile,
    SourceProfile,
)
from schemashift.contracts.schema_map import (
    ApprovalRecord,
    Column,
    Decision,
    ForeignKey,
    Index,
    SchemaMap,
    SourceInfo,
    Table,
)
from schemashift.contracts.similarity import (
    Band,
    EntityScore,
    FieldScore,
    SimilarityReport,
)
from schemashift.contracts.state import GraphState
from schemashift.contracts.verify import CheckResult, VerifyReport

__all__ = [
    "ApprovalRecord",
    "Band",
    "CheckResult",
    "CollectionProfile",
    "Column",
    "Decision",
    "EntityScore",
    "ExplanationNote",
    "FieldProfile",
    "FieldScore",
    "ForeignKey",
    "GraphState",
    "Index",
    "ProposedDecision",
    "RemapPatch",
    "SchemaMap",
    "SchemaProposal",
    "SimilarityReport",
    "SourceInfo",
    "SourceProfile",
    "Table",
    "VerifyReport",
]
