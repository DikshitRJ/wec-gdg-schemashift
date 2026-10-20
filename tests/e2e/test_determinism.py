"""E2E determinism test: two full runs produce identical map_hash and artifacts.

Spec: tests/e2e-determinism
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from schemashift.graph.runner import MigrationRunner
from schemashift.seed.shop import seed_shop


@pytest.mark.e2e
def test_two_runs_identical_artifacts(mongo_client, tmp_path: Path) -> None:
    """Verify two runs produce byte-identical artifacts and match golden copies."""
    out_dir = Path("workspace/out")
    golden_dir = Path("examples/shop/golden")

    # Run 1
    seed_shop(mongo_client)
    runner1 = MigrationRunner()
    for _ in runner1.run(
        config_path="workspace/schemashift.yaml",
        ci_mode=True,
        provider="none",
        run_id="det-run-1",
    ):
        pass

    run1_files = {}
    for base in ["migrations", "etl", "orm"]:
        for p in (out_dir / base).rglob("*"):
            if p.is_file() and "__pycache__" not in str(p):
                run1_files[str(p.relative_to(out_dir))] = p.read_bytes()
    run1_files["schema_map.frozen.json"] = (out_dir / "schema_map.frozen.json").read_bytes()

    # Run 2
    shutil.rmtree(out_dir, ignore_errors=True)
    seed_shop(mongo_client)
    runner2 = MigrationRunner()
    for _ in runner2.run(
        config_path="workspace/schemashift.yaml",
        ci_mode=True,
        provider="none",
        run_id="det-run-2",
    ):
        pass

    run2_files = {}
    for base in ["migrations", "etl", "orm"]:
        for p in (out_dir / base).rglob("*"):
            if p.is_file() and "__pycache__" not in str(p):
                run2_files[str(p.relative_to(out_dir))] = p.read_bytes()
    run2_files["schema_map.frozen.json"] = (out_dir / "schema_map.frozen.json").read_bytes()

    # Compare Run 1 vs Run 2
    assert set(run1_files.keys()) == set(run2_files.keys())
    for rel_path, b1 in run1_files.items():
        assert b1 == run2_files[rel_path], f"File {rel_path} differed between run 1 and run 2"

    # Compare against golden
    if golden_dir.exists():
        assert (golden_dir / "migrations" / "001_schema.sql").read_bytes() == run1_files[
            "migrations/001_schema.sql"
        ]
        assert (golden_dir / "schema_map.frozen.json").read_bytes() == run1_files[
            "schema_map.frozen.json"
        ]
