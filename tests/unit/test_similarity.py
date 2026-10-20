"""Unit tests for similarity module.

Spec: similarity/unit-test
"""

from schemashift.config import ScoringConfig
from schemashift.contracts.profile import CollectionProfile, FieldProfile, SourceProfile
from schemashift.contracts.schema_map import Column, SchemaMap, Table
from schemashift.contracts.similarity import Band
from schemashift.normalize import normalize_name, normalize_type
from schemashift.similarity.report import build_similarity_report


def test_normalize():
    assert normalize_name("userId") == "user"
    assert normalize_name("order_items") == "order item"
    assert normalize_type("int32") == "int"
    assert normalize_type("Decimal128") == "decimal"
    assert normalize_type("timestamptz") == "timestamp"


def test_similarity_scoring():
    fp = FieldProfile(path="email", types={"string": 10}, presence_rate=1.0)
    col = Column(name="email", pg_type="TEXT", nullable=False)
    table = Table(name="users", origin_collection="users", columns=[col])
    smap = SchemaMap(tables=[table])
    coll = CollectionProfile(name="users", fields=[fp])
    profile = SourceProfile(database="shop", collections=[coll])

    cfg = ScoringConfig()
    report = build_similarity_report(profile, smap, cfg)

    assert report.overall_band == Band.MATCHED
    assert report.total_fields == 1
    assert report.matched_fields == 1
