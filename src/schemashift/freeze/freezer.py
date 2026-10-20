"""Freezer: atomic write, hash verification, version bump, and approval ledger.

Spec: freeze-gate/freezer
"""

from __future__ import annotations

import contextlib
import json
import os
import stat
from datetime import UTC, datetime
from pathlib import Path

from schemashift.contracts.schema_map import ApprovalRecord, SchemaMap
from schemashift.errors import FreezeError
from schemashift.freeze.canonical import compute_map_hash


def freeze_map(
    schema_map: SchemaMap,
    out_dir: str | Path,
    approvals: list[ApprovalRecord] | None = None,
) -> tuple[SchemaMap, str]:
    """Freeze a SchemaMap atomically with map_hash, chmod 444, and update ledger.

    Returns (frozen_schema_map, path_to_frozen_file).
    """
    out_path = Path(out_dir)
    state_dir = out_path / "state"
    maps_dir = state_dir / "maps"
    maps_dir.mkdir(parents=True, exist_ok=True)

    # 1. Compute canonical hash
    calculated_hash = compute_map_hash(schema_map)
    schema_map.map_hash = calculated_hash

    # 2. Archive versioned map
    version_file = maps_dir / f"v{schema_map.map_version}.json"
    version_content = schema_map.model_dump_json(indent=2) + "\n"
    version_file.write_text(version_content, encoding="utf-8")

    # 3. Write approval ledger in approvals.jsonl
    if approvals:
        approvals_file = state_dir / "approvals.jsonl"
        with open(approvals_file, "a", encoding="utf-8") as f:
            for app in approvals:
                if not app.timestamp:
                    app.timestamp = datetime.now(UTC).isoformat()
                f.write(app.model_dump_json() + "\n")

    # 4. Atomic write to schema_map.frozen.json
    frozen_target = out_path / "schema_map.frozen.json"
    tmp_target = out_path / f"schema_map.frozen.json.tmp.{os.getpid()}"

    # If target exists and is read-only (chmod 444), remove write protection so we can overwrite
    if frozen_target.exists():
        with contextlib.suppress(OSError):
            frozen_target.chmod(stat.S_IWUSR | stat.S_IRUSR)

    tmp_target.write_text(version_content, encoding="utf-8")
    tmp_target.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)  # 0444 read-only
    tmp_target.replace(frozen_target)

    return schema_map, str(frozen_target.resolve())


def load_frozen_map(file_path: str | Path) -> SchemaMap:
    """Load and verify a frozen SchemaMap. Raises FreezeError if hash mismatch."""
    p = Path(file_path)
    if not p.exists():
        raise FreezeError(
            f"Frozen schema map file '{p}' does not exist.",
            hint="Run the pipeline up to the freeze step first.",
        )

    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        schema_map = SchemaMap.model_validate(data)
    except Exception as exc:
        raise FreezeError(
            f"Corrupt frozen schema map in '{p}': {exc}",
            hint="Re-run the inference and freeze steps.",
        ) from exc

    expected_hash = schema_map.map_hash
    recomputed_hash = compute_map_hash(schema_map)

    if expected_hash != recomputed_hash:
        raise FreezeError(
            f"Frozen map hash mismatch! Recorded '{expected_hash}' but recomputed '{recomputed_hash}'.",
            hint="The schema map may have been tampered with. Re-run freeze.",
        )

    return schema_map
