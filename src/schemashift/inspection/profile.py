"""Build and persist a complete ``SourceProfile`` for a MongoDB database.

Iterates every collection in sorted order, samples documents
deterministically, computes field statistics, redacts examples, and
writes the result to ``reports/profile.json``.

Spec: inspection/profile
"""

from __future__ import annotations

import json
from pathlib import Path

from pymongo import MongoClient

from schemashift.contracts.profile import (
    CollectionProfile,
    SourceProfile,
)
from schemashift.errors import SchemaShiftError
from schemashift.inspection.redact import redact_examples
from schemashift.inspection.sampler import sample_collection
from schemashift.inspection.typestats import compute_field_stats


def build_profile(
    mongo_client: MongoClient,  # type: ignore[type-arg]
    database: str,
    sample_size: int,
) -> SourceProfile:
    """Profile every collection in *database* and return a ``SourceProfile``.

    Parameters
    ----------
    mongo_client:
        An active ``pymongo.MongoClient``.
    database:
        Name of the MongoDB database to inspect.
    sample_size:
        Maximum documents to sample per collection.

    Returns
    -------
    SourceProfile
        Complete profile including all collections and their field stats.

    Raises
    ------
    SchemaShiftError
        If the database is empty or inaccessible.
    """
    if sample_size < 1:
        raise SchemaShiftError(
            f"sample_size must be >= 1, got {sample_size}",
            hint="Pass a positive integer as the sample size.",
        )

    try:
        db = mongo_client[database]
        collection_names = sorted(db.list_collection_names())
    except Exception as exc:
        raise SchemaShiftError(
            f"Cannot list collections in database '{database}': {exc}",
            hint="Check the MongoDB connection URI and permissions.",
        ) from exc

    if not collection_names:
        raise SchemaShiftError(
            f"Database '{database}' has no collections.",
            hint="Verify the database name and that it contains data.",
        )

    collections: list[CollectionProfile] = []

    for coll_name in collection_names:
        coll = db[coll_name]
        docs = sample_collection(coll, sample_size)
        fields = compute_field_stats(docs, coll_name)
        fields = [redact_examples(f) for f in fields]

        doc_count: int
        try:
            doc_count = coll.estimated_document_count()
        except Exception:
            doc_count = len(docs)

        collections.append(
            CollectionProfile(
                name=coll_name,
                doc_count=doc_count,
                sample_count=len(docs),
                fields=fields,
            )
        )

    return SourceProfile(
        database=database,
        collections=collections,
        sample_size=sample_size,
    )


def write_profile(profile: SourceProfile, out_dir: str) -> str:
    """Serialise *profile* to ``<out_dir>/reports/profile.json``.

    Parameters
    ----------
    profile:
        The ``SourceProfile`` to persist.
    out_dir:
        Root output directory (e.g. ``workspace/out``).

    Returns
    -------
    str
        Absolute path of the written JSON file.

    Raises
    ------
    SchemaShiftError
        If the file cannot be written.
    """
    reports_dir = Path(out_dir) / "reports"
    try:
        reports_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise SchemaShiftError(
            f"Cannot create reports directory '{reports_dir}': {exc}",
            hint="Check filesystem permissions for the output directory.",
        ) from exc

    out_path = reports_dir / "profile.json"
    try:
        payload = profile.model_dump(mode="json")
        out_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    except Exception as exc:
        raise SchemaShiftError(
            f"Cannot write profile to '{out_path}': {exc}",
            hint="Check filesystem permissions for the output directory.",
        ) from exc

    return str(out_path.resolve())
