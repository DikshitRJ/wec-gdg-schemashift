"""Unit tests for assist functions, fallbacks, and proposal merging.

Spec: llm-assist/unit-test
"""

from schemashift.assist.fallbacks import (
    fallback_annotate_scripts,
    fallback_diagnose_failures,
    fallback_explain_similarity,
    fallback_schema_proposal,
)
from schemashift.assist.merge import merge_proposals
from schemashift.contracts.llm import ProposedDecision, SchemaProposal
from schemashift.contracts.schema_map import Column, SchemaMap, Table
from schemashift.contracts.similarity import Band, SimilarityReport
from schemashift.migrate.failures import RowFailure


def test_fallbacks():
    report = SimilarityReport(overall_score=0.92, overall_band=Band.MATCHED)
    exp = fallback_explain_similarity(report)
    assert "92.0%" in exp
    assert "MATCHED" in exp

    col = Column(name="attrs", pg_type="JSONB")
    tbl = Table(name="products", columns=[col])
    smap = SchemaMap(tables=[tbl])
    annot = fallback_annotate_scripts(smap)
    assert annot.risk_level == "medium"
    assert any("JSONB" in n for n in annot.notes)

    failures = [
        RowFailure(
            collection="reviews",
            doc_id="1",
            path="rating",
            column="rating",
            value_repr="'great'",
            reason="Uncoercible",
        )
    ]
    patch = fallback_diagnose_failures(failures)
    assert patch.target == "reviews.rating"
    assert patch.changes == {"pg_type": "TEXT", "transform": "identity"}


def test_merge_proposals():
    col = Column(name="user_name", pg_type="TEXT")
    tbl = Table(name="users", columns=[col])
    smap = SchemaMap(tables=[tbl])

    # Valid rename proposal
    prop = ProposedDecision(
        target_path="users.user_name",
        suggestion="username",
        category="rename",
        rationale="More idiomatic",
    )
    proposals = SchemaProposal(proposals=[prop])

    updated = merge_proposals(smap, proposals)
    assert updated.tables[0].columns[0].name == "username"
    assert any(d.provenance == "llm_proposed_validated" for d in updated.decisions)
