"""Record count verification between MongoDB source and PostgreSQL target.

Spec: verify/counts
"""

from __future__ import annotations

from typing import Any
import psycopg
from pymongo import MongoClient

from schemashift.contracts.schema_map import SchemaMap, Table
from schemashift.contracts.verify import CheckResult
from schemashift.identifiers import quote_ident


def verify_counts(
    mongo_client: MongoClient,  # type: ignore[type-arg]
    pg_conn_str: str,
    schema_map: SchemaMap,
) -> list[CheckResult]:
    """Verify record counts between MongoDB and PostgreSQL for all tables."""
    results: list[CheckResult] = []
    db = mongo_client[schema_map.source.database]

    with psycopg.connect(pg_conn_str) as conn:
        with conn.cursor() as cur:
            for table in schema_map.tables:
                # 1. Get actual count from PostgreSQL
                cur.execute(f"SELECT count(*) FROM {quote_ident(table.name)}")
                actual_cnt = cur.fetchone()[0]

                # 2. Get expected count from MongoDB
                expected_cnt = 0
                coll = db[table.origin_collection]

                if table.kind == "root":
                    expected_cnt = coll.count_documents({})
                elif table.kind == "child":
                    # Sum lengths of arrays
                    array_field = table.origin_path.replace("[]", "")
                    pipeline = [
                        {"$project": {"count": {"$size": {"$ifNull": [f"${array_field}", []]}}}},
                        {"$group": {"_id": None, "total": {"$sum": "$count"}}},
                    ]
                    agg = list(coll.aggregate(pipeline))
                    expected_cnt = agg[0]["total"] if agg else 0

                passed = actual_cnt == expected_cnt
                results.append(
                    CheckResult(
                        name="counts",
                        table=table.name,
                        passed=passed,
                        expected=str(expected_cnt),
                        actual=str(actual_cnt),
                        details=f"Expected {expected_cnt} rows from Mongo, found {actual_cnt} in Postgres.",
                    )
                )

    return results
