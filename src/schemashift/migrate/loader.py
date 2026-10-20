"""Batched data loader from MongoDB to PostgreSQL with all-or-nothing semantics.

Spec: migrate/loader
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import psycopg
from pymongo import MongoClient

from schemashift.contracts.schema_map import SchemaMap
from schemashift.errors import MigrationError
from schemashift.gen.etl_plan import generate_etl_plan
from schemashift.identifiers import quote_ident
from schemashift.migrate.failures import RowFailure, write_failures_report
from schemashift.migrate.transforms import TransformError, apply_transform

ProgressCallback = Callable[[str, int, int], None]  # (table_name, loaded_rows, total_rows)


def _extract_nested_value(doc: dict[str, Any], path: str) -> Any:
    """Extract value at dotted path from document."""
    parts = path.split(".")
    curr: Any = doc
    for part in parts:
        if curr is None or not isinstance(curr, dict):
            return None
        curr = curr.get(part)
    return curr


class DataLoader:
    """Coordinates the deterministic migration of data from Mongo to PostgreSQL."""

    def __init__(
        self,
        mongo_uri: str,
        pg_uri: str,
        schema_map: SchemaMap,
        *,
        batch_size: int = 500,
        truncate: bool = False,
        all_or_nothing: bool = True,
        max_retries: int = 3,
        out_dir: str = "workspace/out",
        progress_cb: ProgressCallback | None = None,
    ) -> None:
        self.mongo_uri = mongo_uri
        self.pg_uri = pg_uri
        self.schema_map = schema_map
        self.batch_size = batch_size
        self.truncate = truncate
        self.all_or_nothing = all_or_nothing
        self.max_retries = max_retries
        self.out_dir = out_dir
        self.progress_cb = progress_cb
        self.failures: list[RowFailure] = []

    def load_all(self) -> dict[str, int]:
        """Execute complete data migration. Returns count of rows loaded per table."""
        self.failures.clear()
        etl_plan = generate_etl_plan(self.schema_map)
        ordered_tables = etl_plan["tables"]

        mongo_client: MongoClient[dict[str, Any]] = MongoClient(self.mongo_uri)
        db = mongo_client[self.schema_map.source.database]

        # Check target tables & truncate if requested
        with psycopg.connect(self.pg_uri) as conn:
            with conn.cursor() as cur:
                for tbl in ordered_tables:
                    tbl_name = tbl["name"]
                    cur.execute(f"SELECT count(*) FROM {quote_ident(tbl_name)}")
                    row = cur.fetchone()
                    row_cnt = row[0] if row else 0
                    if row_cnt > 0 and not self.truncate:
                        raise MigrationError(
                            f"Target table '{tbl_name}' is not empty ({row_cnt} rows).",
                            hint="Pass --truncate to allow clearing target tables before migration.",
                        )

            if self.truncate:
                with conn.cursor() as cur:
                    for tbl in reversed(ordered_tables):
                        cur.execute(f"TRUNCATE TABLE {quote_ident(tbl['name'])} CASCADE")
                conn.commit()

        # Connect and load all tables
        results: dict[str, int] = {}

        try:
            with psycopg.connect(self.pg_uri) as conn:
                for tbl in ordered_tables:
                    loaded = self._load_table(db, conn, tbl)
                    results[tbl["name"]] = loaded
                    if self.progress_cb:
                        self.progress_cb(tbl["name"], loaded, loaded)

                if self.failures:
                    write_failures_report(self.failures, self.out_dir)
                    raise MigrationError(
                        f"Migration failed with {len(self.failures)} row-level failure(s). First failure: {self.failures[0].reason}",
                        hint="Check reports/failures.json for full error details.",
                    )

                conn.commit()
        except Exception as exc:
            if not isinstance(exc, MigrationError) and self.failures:
                write_failures_report(self.failures, self.out_dir)
            if not isinstance(exc, MigrationError):
                raise MigrationError(
                    f"Migration aborted due to database error: {exc}",
                    hint="Check database connectivity and PostgreSQL logs.",
                ) from exc
            raise

        return results

    def _load_table(
        self,
        mongo_db: Any,
        pg_conn: psycopg.Connection,
        table_plan: dict[str, Any],
    ) -> int:
        """Load data for a single table."""
        coll_name = table_plan["source_collection"]
        tbl_name = table_plan["name"]
        kind = table_plan["kind"]
        iter_path = table_plan["iteration_path"]
        columns = table_plan["columns"]

        coll = mongo_db[coll_name]
        cursor = coll.find({}).sort("_id", 1)

        # Build INSERT statement
        # Exclude identity columns from INSERT unless specified
        insertable_cols = [c for c in columns if not c.get("identity", False)]
        col_names = [quote_ident(c["name"]) for c in insertable_cols]
        placeholders = ["%s"] * len(insertable_cols)

        sql = f"INSERT INTO {quote_ident(tbl_name)} ({', '.join(col_names)}) VALUES ({', '.join(placeholders)})"

        batch_rows: list[tuple[Any, ...]] = []
        total_loaded = 0

        with pg_conn.cursor() as cur:
            for doc in cursor:
                doc_id_str = str(doc.get("_id", "unknown"))

                if kind == "root":
                    row_vals: list[Any] = []
                    row_failed = False
                    for c in insertable_cols:
                        src_path = c["source_path"]
                        raw_val = _extract_nested_value(doc, src_path) if src_path else None
                        try:
                            val = apply_transform(c["transform"], raw_val, path=src_path)
                            row_vals.append(val)
                        except TransformError as te:
                            self.failures.append(
                                RowFailure(
                                    collection=coll_name,
                                    doc_id=doc_id_str,
                                    path=src_path,
                                    column=c["name"],
                                    value_repr=te.value_repr,
                                    reason=str(te),
                                    hint=te.hint,
                                )
                            )
                            row_failed = True
                            break

                    if not row_failed:
                        batch_rows.append(tuple(row_vals))

                elif kind == "child":
                    # Array expansion
                    array_subpath = iter_path.replace("[]", "")
                    array_val = _extract_nested_value(doc, array_subpath) or []
                    if not isinstance(array_val, list):
                        continue

                    parent_id_val = apply_transform("objectid_hex", doc.get("_id"), path="_id")

                    for idx, item in enumerate(array_val):
                        row_vals = []
                        row_failed = False
                        for c in insertable_cols:
                            c_name = c["name"]
                            if c_name == table_plan.get("parent_fk_col"):
                                row_vals.append(parent_id_val)
                            elif c_name == "position":
                                row_vals.append(idx)
                            elif c_name == "value":
                                # Array of scalars
                                try:
                                    v = apply_transform(c["transform"], item, path=iter_path)
                                    row_vals.append(v)
                                except TransformError as te:
                                    self.failures.append(
                                        RowFailure(
                                            collection=coll_name,
                                            doc_id=doc_id_str,
                                            path=iter_path,
                                            column="value",
                                            value_repr=te.value_repr,
                                            reason=str(te),
                                            hint=te.hint,
                                        )
                                    )
                                    row_failed = True
                                    break
                            else:
                                # Array of objects
                                leaf_prop = (
                                    c["source_path"].split(".")[-1] if c["source_path"] else c_name
                                )
                                raw_v = item.get(leaf_prop) if isinstance(item, dict) else None
                                try:
                                    v = apply_transform(
                                        c["transform"], raw_v, path=c["source_path"]
                                    )
                                    row_vals.append(v)
                                except TransformError as te:
                                    self.failures.append(
                                        RowFailure(
                                            collection=coll_name,
                                            doc_id=doc_id_str,
                                            path=c["source_path"],
                                            column=c_name,
                                            value_repr=te.value_repr,
                                            reason=str(te),
                                            hint=te.hint,
                                        )
                                    )
                                    row_failed = True
                                    break

                        if not row_failed:
                            batch_rows.append(tuple(row_vals))

                # Flush batch if full
                if len(batch_rows) >= self.batch_size:
                    cur.executemany(sql, batch_rows)
                    total_loaded += len(batch_rows)
                    batch_rows.clear()

            # Flush remaining rows
            if batch_rows:
                cur.executemany(sql, batch_rows)
                total_loaded += len(batch_rows)
                batch_rows.clear()

        return total_loaded
