"""Pydantic contracts re-exports.

Spec: foundation/contracts-init
"""

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
from schemashift.contracts.profile import (
    CollectionProfile,
    FieldProfile,
    SourceProfile,
)
from schemashift.contracts.similarity import (
    Band,
    EntityScore,
    FieldScore,
    SimilarityReport,
)
from schemashift.contracts.verify import CheckResult, VerifyReport
from schemashift.contracts.llm import (
    ExplanationNote,
    RemapPatch,
    SchemaProposal,
    ProposedDecision,
)
from schemashift.contracts.state import GraphState

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
