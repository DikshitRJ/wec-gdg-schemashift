"""Build draft SchemaMap from SourceProfile.

Spec: infer/build
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from schemashift.config import Settings
from schemashift.contracts.profile import CollectionProfile, FieldProfile, SourceProfile
from schemashift.contracts.schema_map import (
    Column,
    ForeignKey,
    Index,
    SchemaMap,
    SourceInfo,
    Table,
)
from schemashift.errors import SchemaShiftError
from schemashift.identifiers import quote_ident, safe_name, singularize, snake_case
from schemashift.infer.keys import detect_indexes_and_uniques
from schemashift.infer.nesting import NestingStrategy, decide_nesting_strategy
from schemashift.infer.references import detect_foreign_keys
from schemashift.infer.rules import RuleRegistry
from schemashift.infer.typemap import select_pg_type_and_transform


def build_draft_map(profile: SourceProfile, settings: Settings) -> SchemaMap:
    """Infer a relational schema from SourceProfile."""
    registry = RuleRegistry()
    tables: list[Table] = []
    all_table_names: list[str] = []

    # First pass: determine all root and child tables
    collection_profiles = sorted(profile.collections, key=lambda c: c.name)

    # 1. Identify all tables to be created
    for coll in collection_profiles:
        root_table_name = snake_case(coll.name)
        all_table_names.append(root_table_name)

        # Look for array fields that become child tables
        for field in coll.fields:
            if field.is_array:
                child_subpath = field.path.replace("[]", "")
                child_name = f"{root_table_name}_{snake_case(child_subpath.replace('.', '_'))}"
                all_table_names.append(child_name)

    all_table_names = sorted(set(all_table_names))

    # 2. Build each table
    for coll in collection_profiles:
        root_table_name = snake_case(coll.name)
        root_columns: list[Column] = []
        root_col_mapping: dict[str, str] = {}  # path -> col_name

        # Primary key: id CHAR(24) from _id
        root_columns.append(
            Column(
                name="id",
                pg_type="CHAR(24)",
                nullable=False,
                identity=False,
                source_path="_id",
                transform="objectid_hex",
            )
        )
        root_col_mapping["_id"] = "id"

        # Organize fields
        child_tables_to_make: dict[str, list[FieldProfile]] = {}

        for field in sorted(coll.fields, key=lambda f: f.path):
            if field.path == "_id":
                continue

            # Check if this field belongs to an array
            if "[]" in field.path:
                array_root = field.path.split("[]")[0] + "[]"
                if array_root not in child_tables_to_make:
                    child_tables_to_make[array_root] = []
                child_tables_to_make[array_root].append(field)
                continue

            # Check if this is an array root itself
            if field.is_array:
                if field.path + "[]" not in child_tables_to_make:
                    child_tables_to_make[field.path + "[]"] = []
                continue

            # Nested object or scalar
            if field.is_object:
                child_fields = [f for f in coll.fields if f.path.startswith(f"{field.path}.")]
                strategy, rule_name = decide_nesting_strategy(
                    field,
                    child_fields=child_fields,
                    embed_max_fields=settings.inference.embed_max_fields,
                    jsonb_variance_threshold=settings.inference.jsonb_variance_threshold,
                )
                if strategy == NestingStrategy.JSONB:
                    col_name = safe_name(field.path.replace(".", "_"))
                    root_columns.append(
                        Column(
                            name=col_name,
                            pg_type="JSONB",
                            nullable=field.presence_rate < 0.98,
                            source_path=field.path,
                            transform="json_dump",
                        )
                    )
                    root_col_mapping[field.path] = col_name
                    registry.record_decision(
                        rule=rule_name,
                        choice=f"jsonb:{col_name}",
                        evidence={"key_variance": field.key_variance},
                    )
                continue

            # Check if parent is JSONB
            parts = field.path.split(".")
            if len(parts) > 1:
                parent_path = ".".join(parts[:-1])
                parent_field = next((f for f in coll.fields if f.path == parent_path), None)
                if parent_field and parent_field.is_object:
                    p_strat, _ = decide_nesting_strategy(
                        parent_field,
                        child_fields=[f for f in coll.fields if f.path.startswith(f"{parent_path}.")],
                        embed_max_fields=settings.inference.embed_max_fields,
                        jsonb_variance_threshold=settings.inference.jsonb_variance_threshold,
                    )
                    if p_strat == NestingStrategy.JSONB:
                        # Skip individual columns for JSONB object children
                        continue

            # Regular scalar or flattened field
            col_name = safe_name(field.path.replace(".", "_"))
            pg_type, transform, ambiguous = select_pg_type_and_transform(field)

            root_columns.append(
                Column(
                    name=col_name,
                    pg_type=pg_type,
                    nullable=field.presence_rate < 0.98,
                    source_path=field.path,
                    transform=transform,
                )
            )
            root_col_mapping[field.path] = col_name

            if ambiguous:
                registry.record_decision(
                    rule="AMBIGUOUS_TYPE_COERCION",
                    choice=f"{col_name}:{pg_type}",
                    evidence={"types": field.types},
                    ambiguity=True,
                )

        # Detect indexes & foreign keys for root table
        indexes = detect_indexes_and_uniques(coll.fields, root_col_mapping)
        fks = detect_foreign_keys(
            coll.name,
            root_table_name,
            [c.name for c in root_columns],
            all_table_names,
        )

        tables.append(
            Table(
                name=root_table_name,
                kind="root",
                origin_collection=coll.name,
                origin_path="",
                primary_key=["id"],
                columns=root_columns,
                foreign_keys=fks,
                indexes=indexes,
            )
        )

        # 3. Build child tables from arrays
        for array_path, subfields in sorted(child_tables_to_make.items()):
            child_clean_path = array_path.replace("[]", "")
            child_table_name = f"{root_table_name}_{snake_case(child_clean_path.replace('.', '_'))}"
            parent_fk_col = f"{singularize(root_table_name)}_id"

            child_cols: list[Column] = [
                Column(
                    name="id",
                    pg_type="BIGINT",
                    identity=True,
                    nullable=False,
                ),
                Column(
                    name=parent_fk_col,
                    pg_type="CHAR(24)",
                    nullable=False,
                    source_path="_id",
                    transform="objectid_hex",
                ),
                Column(
                    name="position",
                    pg_type="INTEGER",
                    nullable=False,
                    source_path="$index",
                ),
            ]

            child_fks = [
                ForeignKey(
                    columns=[parent_fk_col],
                    ref_table=root_table_name,
                    ref_columns=["id"],
                    on_delete="CASCADE",
                )
            ]

            # If array of scalars
            scalar_elem = next((f for f in subfields if f.path == array_path), None)
            if scalar_elem and not any("." in f.path[len(array_path):] for f in subfields if f.path != array_path):
                pg_type, transform, amb = select_pg_type_and_transform(scalar_elem)
                child_cols.append(
                    Column(
                        name="value",
                        pg_type=pg_type,
                        nullable=False,
                        source_path=array_path,
                        transform=transform,
                    )
                )
            else:
                # Array of objects
                prefix_len = len(array_path) + 1  # e.g. "items[]."
                for sf in sorted(subfields, key=lambda f: f.path):
                    if sf.path == array_path or sf.is_object or sf.is_array:
                        continue
                    leaf_name = sf.path[prefix_len:] if sf.path.startswith(array_path + ".") else sf.path
                    col_name = safe_name(leaf_name.replace(".", "_"))
                    pg_type, transform, amb = select_pg_type_and_transform(sf)
                    child_cols.append(
                        Column(
                            name=col_name,
                            pg_type=pg_type,
                            nullable=sf.presence_rate < 0.98,
                            source_path=sf.path,
                            transform=transform,
                        )
                    )

            # Detect additional foreign keys (e.g. product_sku in order_items)
            additional_fks = detect_foreign_keys(
                coll.name,
                child_table_name,
                [c.name for c in child_cols],
                all_table_names,
            )
            for afk in additional_fks:
                if afk.columns != [parent_fk_col]:
                    child_fks.append(afk)

            child_indexes = [
                Index(columns=[parent_fk_col], unique=False)
            ]

            tables.append(
                Table(
                    name=child_table_name,
                    kind="child",
                    origin_collection=coll.name,
                    origin_path=array_path,
                    primary_key=["id"],
                    columns=child_cols,
                    foreign_keys=child_fks,
                    indexes=child_indexes,
                )
            )

            registry.record_decision(
                rule="ARRAY_TO_CHILD_TABLE",
                choice=f"table:{child_table_name}",
                evidence={"array_path": array_path},
            )

    return SchemaMap(
        map_version=1,
        map_hash="",
        source=SourceInfo(
            kind="mongodb",
            database=profile.database,
            collections=[c.name for c in collection_profiles],
        ),
        tables=tables,
        decisions=registry.decisions,
    )
