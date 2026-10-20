"""Per-path type-frequency and statistics walker.

Walks sampled documents, flattens every path (using ``[]`` for array
elements), and accumulates BSON-type counts, string/numeric/array
statistics, distinct-value estimates, and key-set signatures.

Spec: inspection/typestats
"""

from __future__ import annotations

import hashlib
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from typing import Any

from bson import Decimal128, ObjectId

from schemashift.contracts.profile import FieldProfile

# ---------------------------------------------------------------------------
# BSON type detection
# ---------------------------------------------------------------------------


def _bson_type_name(value: Any) -> str:
    """Return a canonical BSON type string for *value*."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "double"
    if isinstance(value, Decimal128):
        return "decimal"
    if isinstance(value, Decimal):
        return "decimal"
    if isinstance(value, str):
        return "string"
    if isinstance(value, bytes):
        return "binData"
    if isinstance(value, ObjectId):
        return "objectId"
    if isinstance(value, datetime):
        return "date"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


# ---------------------------------------------------------------------------
# Accumulator for a single field path
# ---------------------------------------------------------------------------

_DISTINCT_CAP = 1000


class _PathAccumulator:
    """Accumulates statistics for one dotted path."""

    __slots__ = (
        "array_lengths",
        "decimal_max_digits",
        "distinct_capped",
        "distinct_values",
        "examples",
        "is_array",
        "is_object",
        "key_signatures",
        "numeric_values",
        "present",
        "string_lengths",
        "type_counts",
    )

    def __init__(self) -> None:
        self.type_counts: dict[str, int] = defaultdict(int)
        self.present: int = 0
        self.string_lengths: list[int] = []
        self.numeric_values: list[float] = []
        self.decimal_max_digits: int = 0
        self.distinct_values: set[str] = set()
        self.distinct_capped: bool = False
        self.array_lengths: list[int] = []
        self.key_signatures: list[str] = []
        self.examples: list[Any] = []
        self.is_array: bool = False
        self.is_object: bool = False

    # -- recording ----------------------------------------------------------

    def record(self, value: Any) -> None:
        """Record one occurrence of *value* at this path."""
        self.present += 1
        btype = _bson_type_name(value)
        self.type_counts[btype] += 1

        if btype == "string":
            self.string_lengths.append(len(value))
        elif btype in ("int", "double"):
            self.numeric_values.append(float(value))
        elif btype == "decimal":
            dec_str = str(value)
            if "." in dec_str:
                digits = len(dec_str.rsplit(".", 1)[1])
                self.decimal_max_digits = max(self.decimal_max_digits, digits)
            self.numeric_values.append(float(str(value)))
        elif btype == "array":
            self.is_array = True
            self.array_lengths.append(len(value))
        elif btype == "object":
            self.is_object = True
            sig = ",".join(sorted(value.keys()))
            self.key_signatures.append(sig)

        # Track distinct values (hash to keep memory bounded).
        if not self.distinct_capped:
            h = hashlib.sha256(repr(value).encode()).hexdigest()[:16]
            self.distinct_values.add(h)
            if len(self.distinct_values) > _DISTINCT_CAP:
                self.distinct_capped = True

        # Collect up to 3 examples.
        if len(self.examples) < 3:
            self.examples.append(value)

    # -- finalisation -------------------------------------------------------

    def to_field_profile(self, path: str, total_docs: int) -> FieldProfile:
        """Build a ``FieldProfile`` from accumulated data."""
        types = dict(sorted(self.type_counts.items()))
        presence_rate = round(self.present / total_docs, 6) if total_docs else 0.0

        string_lengths: dict[str, int | float] = {}
        if self.string_lengths:
            string_lengths = {
                "min": min(self.string_lengths),
                "max": max(self.string_lengths),
                "mean": round(sum(self.string_lengths) / len(self.string_lengths), 2),
            }

        numeric_range: dict[str, float] = {}
        if self.numeric_values:
            numeric_range = {
                "min": min(self.numeric_values),
                "max": max(self.numeric_values),
            }

        array_lengths: dict[str, float] = {}
        if self.array_lengths:
            array_lengths = {
                "min": float(min(self.array_lengths)),
                "max": float(max(self.array_lengths)),
                "mean": round(sum(self.array_lengths) / len(self.array_lengths), 2),
            }

        # Key-set variance: 0 = all identical, 1 = all unique.
        unique_sigs = sorted(set(self.key_signatures))
        key_variance = 0.0
        if len(self.key_signatures) > 1:
            key_variance = round((len(unique_sigs) - 1) / (len(self.key_signatures) - 1), 6)

        distinct_estimate = len(self.distinct_values)
        is_unique = distinct_estimate == self.present and not self.distinct_capped

        return FieldProfile(
            path=path,
            types=types,
            presence_rate=presence_rate,
            total_docs=total_docs,
            string_lengths=string_lengths,
            numeric_range=numeric_range,
            decimal_digits=self.decimal_max_digits,
            distinct_estimate=distinct_estimate,
            array_lengths=array_lengths,
            key_set_signatures=unique_sigs,
            key_variance=key_variance,
            examples=self.examples[:3],
            is_unique=is_unique,
            is_array=self.is_array,
            is_object=self.is_object,
        )


# ---------------------------------------------------------------------------
# Recursive document walker
# ---------------------------------------------------------------------------


def _walk(
    value: Any,
    prefix: str,
    accumulators: dict[str, _PathAccumulator],
) -> None:
    """Recursively walk *value* and feed path accumulators."""
    if prefix not in accumulators:
        accumulators[prefix] = _PathAccumulator()
    accumulators[prefix].record(value)

    if isinstance(value, dict):
        for key in sorted(value.keys()):
            child_path = f"{prefix}.{key}" if prefix else key
            _walk(value[key], child_path, accumulators)
    elif isinstance(value, list):
        elem_prefix = f"{prefix}[]"
        for item in value:
            _walk(item, elem_prefix, accumulators)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def compute_field_stats(
    docs: list[dict[str, Any]],
    collection_name: str,
) -> list[FieldProfile]:
    """Walk *docs* and return sorted ``FieldProfile`` list.

    Parameters
    ----------
    docs:
        Sampled documents (list of dicts).
    collection_name:
        Name of the source collection (currently unused but passed for
        logging parity).

    Returns
    -------
    list[FieldProfile]
        One entry per unique dotted path, sorted by path.
    """
    total_docs = len(docs)
    if total_docs == 0:
        return []

    accumulators: dict[str, _PathAccumulator] = {}
    for doc in docs:
        # Walk top-level keys only (skip the implicit root object).
        for key in sorted(doc.keys()):
            _walk(doc[key], key, accumulators)

    return [acc.to_field_profile(path, total_docs) for path, acc in sorted(accumulators.items())]
