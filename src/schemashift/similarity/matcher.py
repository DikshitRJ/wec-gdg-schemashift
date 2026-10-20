"""Source field to target column pairing.

Spec: similarity/matcher
"""

from __future__ import annotations

from typing import Any
from schemashift.contracts.profile import FieldProfile, SourceProfile
from schemashift.contracts.schema_map import Column, SchemaMap, Table


class MatchedPair:
    """A matched pairing between source field and target column/table."""

    def __init__(
        self,
        collection: str,
        field: FieldProfile,
        table: Table | None = None,
        column: Column | None = None,
    ) -> None:
        self.collection = collection
        self.field = field
        self.table = table
        self.column = column


def pair_fields(
    profile: SourceProfile,
    schema_map: SchemaMap,
) -> list[MatchedPair]:
    """Pair each source field with its target column and table."""
    pairs: list[MatchedPair] = []

    # Map tables by collection origin
    tables_by_coll: dict[str, list[Table]] = {}
    for table in schema_map.tables:
        coll = table.origin_collection
        if coll not in tables_by_coll:
            tables_by_coll[coll] = []
        tables_by_coll[coll].append(table)

    for coll_prof in profile.collections:
        coll_tables = tables_by_coll.get(coll_prof.name, [])
        for field in coll_prof.fields:
            # Skip root _id mapping to itself
            if field.path == "_id":
                continue

            matched_col: Column | None = None
            matched_tbl: Table | None = None

            for tbl in coll_tables:
                for col in tbl.columns:
                    # Check exact source path match or col name match
                    if col.source_path == field.path or (not col.source_path and col.name == field.path):
                        matched_col = col
                        matched_tbl = tbl
                        break
                    # Check array element path match (e.g. items[].sku matching items.sku)
                    if col.source_path and field.path.replace("[]", "") == col.source_path.replace("[]", ""):
                        matched_col = col
                        matched_tbl = tbl
                        break
                if matched_col:
                    break

            pairs.append(
                MatchedPair(
                    collection=coll_prof.name,
                    field=field,
                    table=matched_tbl,
                    column=matched_col,
                )
            )

    return pairs
