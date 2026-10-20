"""Unit tests for schema inference.

Spec: infer/unit-test
"""

from schemashift.config import Settings
from schemashift.contracts.profile import CollectionProfile, FieldProfile, SourceProfile
from schemashift.infer.build import build_draft_map
from schemashift.infer.typemap import select_pg_type_and_transform


def test_typemap():
    fp_int = FieldProfile(path="age", types={"int": 10}, presence_rate=1.0)
    pg_type, transform, amb = select_pg_type_and_transform(fp_int)
    assert pg_type == "INTEGER"
    assert transform == "identity"
    assert not amb

    fp_mixed = FieldProfile(path="rating", types={"int": 85, "string": 15}, presence_rate=1.0)
    pg_type, transform, amb = select_pg_type_and_transform(fp_mixed)
    assert pg_type == "SMALLINT"
    assert transform == "int_coerce"
    assert amb


def test_build_draft_map():
    fields = [
        FieldProfile(path="_id", types={"objectId": 10}, presence_rate=1.0),
        FieldProfile(path="email", types={"string": 10}, presence_rate=1.0, is_unique=True),
        FieldProfile(path="tags[]", types={"string": 20}, presence_rate=1.0, is_array=True),
    ]
    coll = CollectionProfile(name="users", doc_count=10, sample_count=10, fields=fields)
    profile = SourceProfile(database="shop", collections=[coll], sample_size=10)

    settings = Settings()
    smap = build_draft_map(profile, settings)

    table_names = [t.name for t in smap.tables]
    assert "users" in table_names
    assert "users_tags" in table_names

    users_table = next(t for t in smap.tables if t.name == "users")
    assert any(c.name == "email" for c in users_table.columns)
    assert any(idx.unique for idx in users_table.indexes)

    tags_table = next(t for t in smap.tables if t.name == "users_tags")
    assert any(c.name == "user_id" for c in tags_table.columns)
    assert any(c.name == "position" for c in tags_table.columns)
    assert any(c.name == "value" for c in tags_table.columns)
