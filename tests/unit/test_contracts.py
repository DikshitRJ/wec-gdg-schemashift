"""Unit tests for contract models.

Spec: foundation/contracts-test
"""

import pytest
from pydantic import ValidationError

from schemashift.contracts import (
    Band,
    Column,
    Decision,
    EntityScore,
    FieldScore,
    ForeignKey,
    Index,
    SchemaMap,
    SimilarityReport,
    SourceInfo,
    Table,
)


def test_schema_map_contract():
    col = Column(name="id", pg_type="CHAR(24)", nullable=False)
    fk = ForeignKey(columns=["user_id"], ref_table="users", ref_columns=["id"])
    idx = Index(columns=["user_id"], unique=False)
    table = Table(
        name="orders",
        kind="root",
        primary_key=["id"],
        columns=[col],
        foreign_keys=[fk],
        indexes=[idx],
    )
    decision = Decision(id="D1", rule="TEST_RULE", choice="table:orders")
    smap = SchemaMap(
        map_version=1,
        map_hash="sha256:abc",
        source=SourceInfo(kind="mongodb", database="shop", collections=["orders"]),
        tables=[table],
        decisions=[decision],
    )
    assert smap.tables[0].name == "orders"
    assert smap.tables[0].columns[0].name == "id"


def test_extra_fields_forbidden():
    with pytest.raises(ValidationError):
        Column(name="id", pg_type="TEXT", nonexistent_field="bad")  # type: ignore[call-arg]


def test_similarity_report_contract():
    fs = FieldScore(
        source_path="users.name",
        target_column="name",
        target_table="users",
        name_score=1.0,
        type_score=1.0,
        structure_score=1.0,
        constraint_score=1.0,
        total=1.0,
        band=Band.MATCHED,
    )
    es = EntityScore(
        collection="users",
        tables=["users"],
        field_scores=[fs],
        total=1.0,
        field_count=1,
        matched_count=1,
    )
    report = SimilarityReport(
        overall_score=1.0,
        overall_band=Band.MATCHED,
        entity_scores=[es],
        total_fields=1,
        matched_fields=1,
    )
    assert report.overall_band == Band.MATCHED
