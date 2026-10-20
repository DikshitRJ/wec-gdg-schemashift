"""Canonical JSON serialization and hashing for SchemaMap.

Spec: freeze-gate/canonical
"""

from __future__ import annotations

import hashlib
import json
from schemashift.contracts.schema_map import SchemaMap


def canonical_json(schema_map: SchemaMap) -> str:
    """Produce deterministic canonical JSON representation of SchemaMap.

    Excludes volatile fields like map_hash itself and external approvals.
    Keys are strictly sorted, separators are without whitespace.
    """
    payload = {
        "source": schema_map.source.model_dump(),
        "tables": [t.model_dump() for t in sorted(schema_map.tables, key=lambda t: t.name)],
        "decisions": [
            {
                "id": d.id,
                "rule": d.rule,
                "choice": d.choice,
                "provenance": d.provenance,
            }
            for d in sorted(schema_map.decisions, key=lambda d: d.id)
        ],
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_map_hash(schema_map: SchemaMap) -> str:
    """Compute sha256 checksum of canonical JSON."""
    canon = canonical_json(schema_map).encode("utf-8")
    digest = hashlib.sha256(canon).hexdigest()
    return f"sha256:{digest}"
