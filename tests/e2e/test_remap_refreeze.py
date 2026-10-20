"""E2E test verifying remap and refreeze updates map_hash and generated scripts.

Spec: tests/e2e-remap-refreeze
"""

from __future__ import annotations

from pathlib import Path

import pytest

from schemashift.freeze.freezer import freeze_map, load_frozen_map
from schemashift.freeze.overrides import apply_overrides
from schemashift.gen.ddl import generate_ddl_sql
from schemashift.graph.runner import MigrationRunner
from schemashift.seed.shop import seed_shop


@pytest.mark.e2e
def test_remap_and_refreeze(mongo_client, tmp_path: Path) -> None:
    """Verify that applying an override produces a different map_hash and updated DDL."""
    seed_shop(mongo_client)
    runner = MigrationRunner()
    run_id = "test-refreeze"

    for _ in runner.run(
        config_path="workspace/schemashift.yaml",
        ci_mode=True,
        provider="none",
        run_id=run_id,
    ):
        pass

    frozen1 = load_frozen_map("workspace/out/schema_map.frozen.json")
    hash1 = frozen1.map_hash
    ddl1 = generate_ddl_sql(frozen1)

    # Apply an override to rename a column in the frozen map
    overrides = [
        {
            "target": "users.email",
            "set": {
                "rename": "user_email_address",
            },
        }
    ]
    modified_map = apply_overrides(frozen1, overrides)
    modified_map.map_version = 2
    frozen2, _frozen2_path = freeze_map(modified_map, tmp_path)
    ddl2 = generate_ddl_sql(frozen2)

    # Checksums must be distinct
    assert hash1 != frozen2.map_hash
    assert frozen2.map_version == 2
    assert "user_email_address" in ddl2
    assert "user_email_address" not in ddl1
