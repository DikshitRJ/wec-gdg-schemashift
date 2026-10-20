"""Validate and merge LLM proposals into SchemaMap.

Spec: llm-assist/merge
"""

from __future__ import annotations

from rapidfuzz import fuzz

from schemashift.contracts.llm import SchemaProposal
from schemashift.contracts.schema_map import Decision, SchemaMap
from schemashift.identifiers import safe_name


def merge_proposals(
    schema_map: SchemaMap,
    proposals: SchemaProposal,
) -> SchemaMap:
    """Validate LLM proposals and apply accepted ones to the SchemaMap."""
    if not proposals or not proposals.proposals:
        return schema_map

    for prop in proposals.proposals:
        target = prop.target_path
        parts = target.split(".")

        # 1. Table rename proposal
        if len(parts) == 1 and prop.category == "rename":
            curr_name = parts[0]
            new_name = safe_name(prop.suggestion)
            # Validator: non-empty, legal name, not collision, name similarity >= 0.5
            sim = fuzz.token_set_ratio(curr_name, new_name) / 100.0
            collision = any(t.name == new_name for t in schema_map.tables)

            if sim >= 0.5 and not collision and new_name:
                for tbl in schema_map.tables:
                    if tbl.name == curr_name:
                        tbl.name = new_name
                        schema_map.decisions.append(
                            Decision(
                                id=f"D-llm-{len(schema_map.decisions) + 1:03d}",
                                rule="LLM_TABLE_RENAME",
                                choice=f"{curr_name}->{new_name}",
                                evidence={"similarity": sim, "rationale": prop.rationale},
                                provenance="llm_proposed_validated",
                            )
                        )

        # 2. Column rename proposal
        elif len(parts) == 2 and prop.category == "rename":
            tbl_name, col_name = parts[0], parts[1]
            new_col = safe_name(prop.suggestion)
            sim = fuzz.token_set_ratio(col_name, new_col) / 100.0

            for tbl in schema_map.tables:
                if tbl.name == tbl_name or tbl.origin_collection == tbl_name:
                    collision = any(c.name == new_col for c in tbl.columns)
                    if sim >= 0.5 and not collision and new_col:
                        for col in tbl.columns:
                            if col.name == col_name:
                                col.name = new_col
                                schema_map.decisions.append(
                                    Decision(
                                        id=f"D-llm-{len(schema_map.decisions) + 1:03d}",
                                        rule="LLM_COLUMN_RENAME",
                                        choice=f"{tbl.name}.{col_name}->{new_col}",
                                        evidence={"similarity": sim, "rationale": prop.rationale},
                                        provenance="llm_proposed_validated",
                                    )
                                )

    return schema_map
