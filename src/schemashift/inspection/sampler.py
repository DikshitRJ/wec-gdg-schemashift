"""Deterministic systematic sampling of a MongoDB collection.

Orders documents by ``_id`` ascending, then selects every *stride*-th
document so that exactly ``sample_size`` (or fewer, if the collection is
smaller) documents are returned.  ``$sample`` is intentionally avoided
because it is non-deterministic.

Spec: inspection/sampler
"""

from __future__ import annotations

import math
from typing import Any

from pymongo.collection import Collection

from schemashift.errors import SchemaShiftError


def sample_collection(
    collection: Collection,  # type: ignore[type-arg]
    sample_size: int,
) -> list[dict[str, Any]]:
    """Return a deterministic sample of documents from *collection*.

    Parameters
    ----------
    collection:
        A ``pymongo.collection.Collection`` handle.
    sample_size:
        Maximum number of documents to return.

    Returns
    -------
    list[dict[str, Any]]
        Documents in ``_id``-ascending order.

    Raises
    ------
    SchemaShiftError
        If *sample_size* is not a positive integer or the collection
        cannot be read.
    """
    if sample_size < 1:
        raise SchemaShiftError(
            f"sample_size must be >= 1, got {sample_size}",
            hint="Pass a positive integer as the sample size.",
        )

    try:
        count = collection.estimated_document_count()
    except Exception as exc:
        raise SchemaShiftError(
            f"Cannot read collection '{collection.name}': {exc}",
            hint="Check the MongoDB connection URI and permissions.",
        ) from exc

    if count == 0:
        return []

    # Full scan when the collection fits inside the requested sample.
    if count <= sample_size:
        return list(collection.find().sort("_id", 1))

    # Systematic stride sampling: fetch every stride-th document.
    stride = math.ceil(count / sample_size)
    docs: list[dict[str, Any]] = []
    cursor = collection.find().sort("_id", 1)
    for idx, doc in enumerate(cursor):
        if idx % stride == 0:
            docs.append(doc)
            if len(docs) >= sample_size:
                break

    return docs
