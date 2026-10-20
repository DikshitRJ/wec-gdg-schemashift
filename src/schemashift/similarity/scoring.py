"""Field, entity, and overall similarity scoring engine.

Spec: similarity/scoring
"""

from __future__ import annotations

from rapidfuzz import distance, fuzz
from schemashift.config import ScoringConfig
from schemashift.contracts.profile import FieldProfile
from schemashift.contracts.schema_map import Column, Table
from schemashift.contracts.similarity import Band, FieldScore
from schemashift.normalize import normalize_name, normalize_type

_COMPATIBILITY_MATRIX = {
    ("int", "int"): 1.0,
    ("float", "float"): 1.0,
    ("decimal", "decimal"): 1.0,
    ("int", "decimal"): 0.9,
    ("int", "float"): 0.8,
    ("text", "text"): 1.0,
    ("bool", "bool"): 1.0,
    ("timestamp", "timestamp"): 1.0,
    ("json", "json"): 1.0,
    ("ref", "ref"): 1.0,
    ("bytes", "bytes"): 1.0,
    # Fallback to jsonb
    ("json", "text"): 0.6,
    ("array", "json"): 0.8,
    ("array", "array"): 1.0,
    ("null", "text"): 0.7,
}


def score_field(
    field: FieldProfile,
    column: Column | None,
    table: Table | None,
    config: ScoringConfig,
) -> FieldScore:
    """Score a single source field against its target column."""
    if column is None:
        return FieldScore(
            source_path=field.path,
            target_column="",
            target_table="",
            name_score=0.0,
            type_score=0.0,
            structure_score=0.0,
            constraint_score=0.0,
            total=0.0,
            band=Band.NEEDS_REVIEW,
            reason_codes=["UNMAPPED"],
            capped=False,
        )

    # 1. Name score
    norm_source_name = normalize_name(field.path)
    norm_target_name = normalize_name(column.name)
    token_ratio = fuzz.token_set_ratio(norm_source_name, norm_target_name) / 100.0
    jw_sim = distance.JaroWinkler.similarity(norm_source_name, norm_target_name)
    name_score = round((token_ratio + jw_sim) / 2.0, 4)

    # 2. Type score
    types = field.types or {"string": 1}
    dominant_bson = max(types.keys(), key=lambda t: types[t])
    total_samples = sum(types.values())
    purity = types[dominant_bson] / total_samples if total_samples else 1.0

    src_fam = normalize_type(dominant_bson)
    tgt_fam = normalize_type(column.pg_type)

    base_type_compat = _COMPATIBILITY_MATRIX.get((src_fam, tgt_fam), 0.5 if src_fam == tgt_fam else 0.3)
    type_score = round(base_type_compat * purity, 4)

    # 3. Structure score
    structure_score = 1.0
    reason_codes: list[str] = []

    if field.is_array:
        if column.pg_type == "JSONB":
            structure_score = 0.6
            reason_codes.append("STRUCT_JSONB_FALLBACK")
        else:
            structure_score = 1.0
    elif field.is_object:
        if column.pg_type == "JSONB":
            structure_score = 0.7
            reason_codes.append("STRUCT_JSONB_FALLBACK")
        else:
            structure_score = 0.9  # Flattened
    else:
        structure_score = 1.0

    # 4. Constraints score
    constraint_score = 1.0
    if not column.nullable and field.presence_rate < 0.98:
        constraint_score = 0.5
        reason_codes.append("NULLABILITY_MISMATCH")

    # Aggregate total
    w = config.weights
    raw_total = (
        w.name * name_score
        + w.type * type_score
        + w.structure * structure_score
        + w.constraints * constraint_score
    )

    # Ambiguity cap
    capped = False
    if purity < 0.95 or len(types) > 1:
        reason_codes.append("TYPE_PURITY_LOW")
        if raw_total > 0.80:
            raw_total = 0.80
            capped = True

    total = round(min(1.0, max(0.0, raw_total)), 4)

    # Band
    if total >= config.matched:
        band = Band.MATCHED
    elif total >= config.guessed:
        band = Band.GUESSED
    else:
        band = Band.NEEDS_REVIEW

    return FieldScore(
        source_path=field.path,
        target_column=column.name,
        target_table=table.name if table else "",
        name_score=name_score,
        type_score=type_score,
        structure_score=structure_score,
        constraint_score=constraint_score,
        total=total,
        band=band,
        reason_codes=sorted(reason_codes),
        capped=capped,
    )
