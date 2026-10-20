"""Primary key and unique index candidate detection.

Spec: infer/keys
"""

from __future__ import annotations

from schemashift.contracts.profile import FieldProfile
from schemashift.contracts.schema_map import Index


def detect_indexes_and_uniques(
    fields: list[FieldProfile],
    column_mapping: dict[str, str],
) -> list[Index]:
    """Detect UNIQUE indexes based on field uniqueness and naming hints."""
    indexes: list[Index] = []
    unique_hints = {"email", "sku", "slug", "code", "username"}

    for field in sorted(fields, key=lambda f: f.path):
        if field.path in column_mapping:
            col_name = column_mapping[field.path]
            # Check if name contains hint
            leaf_name = field.path.split(".")[-1].lower()
            if any(h in leaf_name for h in unique_hints) or field.is_unique:
                if field.presence_rate >= 0.98:
                    indexes.append(
                        Index(
                            columns=[col_name],
                            unique=True,
                        )
                    )

    return indexes
