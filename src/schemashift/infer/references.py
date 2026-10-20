"""Foreign key reference detection by name convention and uniqueness.

Spec: infer/references
"""

from __future__ import annotations

import re
from schemashift.contracts.profile import SourceProfile
from schemashift.contracts.schema_map import ForeignKey, Table
from schemashift.identifiers import singularize, snake_case


def detect_foreign_keys(
    collection_name: str,
    table_name: str,
    column_names: list[str],
    all_table_names: list[str],
) -> list[ForeignKey]:
    """Detect foreign key references for a given table based on column names."""
    fks: list[ForeignKey] = []

    # Map possible parent table names
    table_lookup = {t: t for t in all_table_names}
    singular_lookup = {singularize(t): t for t in all_table_names}

    for col in sorted(column_names):
        # 1. Parent relationship for child tables (e.g. order_id -> orders.id)
        if col.endswith("_id") and col != "id":
            prefix = col[:-3]
            target_table = singular_lookup.get(prefix) or table_lookup.get(prefix) or table_lookup.get(f"{prefix}s")
            if target_table and target_table != table_name:
                fks.append(
                    ForeignKey(
                        columns=[col],
                        ref_table=target_table,
                        ref_columns=["id"],
                        on_delete="CASCADE" if table_name.startswith(f"{target_table}_") or table_name.startswith(f"{singularize(target_table)}_") else "NO ACTION",
                    )
                )
        # 2. Reference by SKU (e.g. product_sku -> products.sku)
        elif col.endswith("_sku"):
            prefix = col[:-4]
            target_table = singular_lookup.get(prefix) or table_lookup.get(prefix) or table_lookup.get(f"{prefix}s")
            if target_table:
                fks.append(
                    ForeignKey(
                        columns=[col],
                        ref_table=target_table,
                        ref_columns=["sku"],
                        on_delete="NO ACTION",
                    )
                )

    return fks
