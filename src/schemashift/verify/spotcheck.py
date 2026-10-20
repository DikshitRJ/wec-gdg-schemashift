"""Independent spot-check comparator between Mongo and PostgreSQL.

Spec: verify/spotcheck
"""

from __future__ import annotations

import json
import random
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import psycopg
from bson import Decimal128
from pymongo import MongoClient

from schemashift.contracts.schema_map import SchemaMap
from schemashift.contracts.verify import CheckResult
from schemashift.identifiers import quote_ident


def _normalize_val(val: Any) -> Any:
    if val is None:
        return None
    if isinstance(val, Decimal128):
        return Decimal(str(val))
    if isinstance(val, datetime):
        if val.tzinfo is None:
            val = val.replace(tzinfo=UTC)
        return val.astimezone(UTC)
    if isinstance(val, str):
        trimmed = val.strip()
        if (trimmed.startswith("{") and trimmed.endswith("}")) or (
            trimmed.startswith("[") and trimmed.endswith("]")
        ):
            try:
                return json.loads(trimmed)
            except Exception:
                pass
    return val


def _values_equal(mongo_val: Any, pg_val: Any) -> bool:
    if mongo_val is None and pg_val is None:
        return True
    if mongo_val is None or pg_val is None:
        return False

    m_norm = _normalize_val(mongo_val)
    p_norm = _normalize_val(pg_val)

    if isinstance(m_norm, datetime) and isinstance(p_norm, datetime):
        return m_norm == p_norm

    if isinstance(m_norm, (int, float, Decimal)) and isinstance(p_norm, (int, float, Decimal)):
        try:
            return float(m_norm) == float(p_norm)
        except Exception:
            pass

    if isinstance(m_norm, dict) and isinstance(p_norm, dict):
        return m_norm == p_norm

    if isinstance(m_norm, list) and isinstance(p_norm, list):
        return m_norm == p_norm

    return str(m_norm).strip() == str(p_norm).strip()


def spotcheck_records(
    mongo_client: MongoClient,  # type: ignore[type-arg]
    pg_conn_str: str,
    schema_map: SchemaMap,
    sample_size: int = 50,
) -> list[CheckResult]:
    """Spot-check N sampled records field-by-field using independent comparison."""
    results: list[CheckResult] = []

    # Deterministic RNG based on schema map hash
    seed_val = (
        int(schema_map.map_hash.replace("sha256:", "")[:8], 16) if schema_map.map_hash else 42
    )
    rng = random.Random(seed_val)

    db = mongo_client[schema_map.source.database]

    with psycopg.connect(pg_conn_str) as conn, conn.cursor() as cur:
        # Spot check each root table
        for tbl in schema_map.tables:
            if tbl.kind != "root":
                continue

            coll = db[tbl.origin_collection]
            all_ids = [doc["_id"] for doc in coll.find({}, {"_id": 1}).sort("_id", 1)]
            if not all_ids:
                continue

            sample_count = min(sample_size, len(all_ids))
            sampled_ids = rng.sample(all_ids, sample_count)

            # Fetch docs from Mongo
            mongo_docs = {str(d["_id"]): d for d in coll.find({"_id": {"$in": sampled_ids}})}

            # Fetch corresponding rows from Postgres
            id_strings = list(mongo_docs.keys())
            cur.execute(
                f"SELECT * FROM {quote_ident(tbl.name)} WHERE {quote_ident('id')} = ANY(%s)",
                (id_strings,),
            )
            if not cur.description:
                continue
            col_names = [desc[0] for desc in cur.description]
            pg_rows = {
                r[col_names.index("id")]: dict(zip(col_names, r, strict=False))
                for r in cur.fetchall()
            }

            mismatches: list[str] = []
            for doc_id_str, mongo_doc in mongo_docs.items():
                pg_row = pg_rows.get(doc_id_str)
                if not pg_row:
                    mismatches.append(f"Row id {doc_id_str} missing in PostgreSQL")
                    continue

                # Compare scalar fields that map 1:1
                for col in tbl.columns:
                    if col.name == "id" or not col.source_path or "." in col.source_path:
                        continue
                    mongo_val = mongo_doc.get(col.source_path)
                    pg_val = pg_row.get(col.name)

                    # Independent comparison rules
                    if not _values_equal(mongo_val, pg_val):
                        mismatches.append(
                            f"Mismatch in {tbl.name}.{col.name} for id {doc_id_str}: Mongo={mongo_val} vs PG={pg_val}"
                        )
                        if len(mismatches) > 5:
                            break

            passed = len(mismatches) == 0
            results.append(
                CheckResult(
                    name="spotcheck",
                    table=tbl.name,
                    passed=passed,
                    expected=f"{sample_count} sampled rows match",
                    actual=f"{sample_count - len(mismatches)} rows matched",
                    details="; ".join(mismatches[:3]) if mismatches else "All sampled rows match.",
                )
            )

    return results
