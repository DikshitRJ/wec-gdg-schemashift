"""Unit tests for canonical hash, gate, overrides, and freezer.

Spec: freeze-gate/unit-test
"""

import pytest
from schemashift.contracts.schema_map import Column, Decision, SchemaMap, Table
from schemashift.contracts.similarity import Band, EntityScore, FieldScore, SimilarityReport
from schemashift.errors import FreezeError
from schemashift.freeze.canonical import canonical_json, compute_map_hash
from schemashift.freeze.freezer import freeze_map, load_frozen_map
from schemashift.freeze.gate import evaluate_gate
from schemashift.freeze.overrides import apply_overrides


def test_canonical_json_and_hash():
    col1 = Column(name="id", pg_type="CHAR(24)", nullable=False)
    t1 = Table(name="users", columns=[col1])
    smap1 = SchemaMap(tables=[t1], decisions=[Decision(id="D1", rule="R1", choice="users")])
    smap2 = SchemaMap(tables=[t1], decisions=[Decision(id="D1", rule="R1", choice="users")])

    h1 = compute_map_hash(smap1)
    h2 = compute_map_hash(smap2)
    assert h1 == h2
    assert h1.startswith("sha256:")


def test_freeze_and_load(tmp_path):
    col = Column(name="id", pg_type="CHAR(24)", nullable=False)
    tbl = Table(name="orders", columns=[col])
    smap = SchemaMap(tables=[tbl])

    frozen, path = freeze_map(smap, tmp_path)
    loaded = load_frozen_map(path)
    assert loaded.map_hash == frozen.map_hash
    assert loaded.tables[0].name == "orders"


def test_freeze_tamper_detection(tmp_path):
    col = Column(name="id", pg_type="CHAR(24)", nullable=False)
    tbl = Table(name="orders", columns=[col])
    smap = SchemaMap(tables=[tbl])

    _, path = freeze_map(smap, tmp_path)

    # Tamper with file
    from pathlib import Path
    import stat
    p = Path(path)
    p.chmod(stat.S_IWUSR | stat.S_IRUSR)
    p.write_text(p.read_text().replace("orders", "tampered_orders"))

    with pytest.raises(FreezeError):
        load_frozen_map(path)


def test_overrides():
    col = Column(name="rating", pg_type="SMALLINT", transform="identity")
    tbl = Table(name="reviews", columns=[col])
    smap = SchemaMap(tables=[tbl])

    overrides = [
        {"target": "reviews.rating", "set": {"transform": "int_coerce"}}
    ]
    updated = apply_overrides(smap, overrides)
    assert updated.tables[0].columns[0].transform == "int_coerce"
