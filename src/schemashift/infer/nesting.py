"""Nesting rules: flatten, child table, or JSONB.

Spec: infer/nesting
"""

from __future__ import annotations

from enum import StrEnum

from schemashift.contracts.profile import FieldProfile


class NestingStrategy(StrEnum):
    FLATTEN = "flatten"
    CHILD_TABLE = "child_table"
    JSONB = "jsonb"


def decide_nesting_strategy(
    field: FieldProfile,
    *,
    child_fields: list[FieldProfile],
    embed_max_fields: int = 8,
    jsonb_variance_threshold: float = 0.4,
) -> tuple[NestingStrategy, str]:
    """Decide nesting strategy for an object or array field."""
    if field.is_array:
        # Scalar array vs object array
        has_object_elements = any(
            cf.path.startswith(f"{field.path}[]")
            and (cf.is_object or "." in cf.path[len(field.path) + 2 :])
            for cf in child_fields
        )
        if has_object_elements:
            return NestingStrategy.CHILD_TABLE, "ARRAY_OF_OBJECTS_TO_CHILD"
        return NestingStrategy.CHILD_TABLE, "ARRAY_OF_SCALARS_TO_CHILD"

    if field.is_object:
        # Check variance
        if field.key_variance >= jsonb_variance_threshold:
            return NestingStrategy.JSONB, "FREEFORM_OBJECT_TO_JSONB"

        leaves = [
            cf
            for cf in child_fields
            if cf.path.startswith(f"{field.path}.") and not cf.is_object and not cf.is_array
        ]
        if field.presence_rate >= 0.98 and len(leaves) <= embed_max_fields:
            return NestingStrategy.FLATTEN, "FLATTEN_STABLE_OBJECT"

        return NestingStrategy.JSONB, "WIDE_OR_SPARSE_OBJECT_TO_JSONB"

    return NestingStrategy.FLATTEN, "SCALAR_FIELD"
