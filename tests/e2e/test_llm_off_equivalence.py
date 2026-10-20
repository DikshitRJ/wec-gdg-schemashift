"""E2E test verifying LLM off vs replay equivalence for core artifacts.

Spec: tests/e2e-llm-equivalence
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from schemashift.graph.runner import MigrationRunner
from schemashift.seed.shop import seed_shop


@pytest.mark.e2e
def test_llm_off_equivalence(mongo_client) -> None:
    """Verify provider=none and provider=replay produce identical core artifacts."""
    out_dir = Path("workspace/out")

    # Run 1: provider=none
    seed_shop(mongo_client)
    runner_none = MigrationRunner()
    for _ in runner_none.run(
        config_path="workspace/schemashift.yaml",
        ci_mode=True,
        provider="none",
        run_id="equiv-none",
    ):
        pass

    none_artifacts = {}
    for base in ["migrations", "etl", "orm"]:
        for p in (out_dir / base).rglob("*"):
            # Exclude markdown sidecars which may contain LLM annotations
            if p.is_file() and not p.name.endswith(".md") and "__pycache__" not in str(p):
                none_artifacts[str(p.relative_to(out_dir))] = p.read_bytes()
    none_artifacts["schema_map.frozen.json"] = (out_dir / "schema_map.frozen.json").read_bytes()

    # Run 2: provider=replay
    shutil.rmtree(out_dir, ignore_errors=True)
    seed_shop(mongo_client)
    runner_replay = MigrationRunner()
    for _ in runner_replay.run(
        config_path="workspace/schemashift.yaml",
        ci_mode=True,
        provider="replay",
        run_id="equiv-replay",
    ):
        pass

    replay_artifacts = {}
    for base in ["migrations", "etl", "orm"]:
        for p in (out_dir / base).rglob("*"):
            if p.is_file() and not p.name.endswith(".md") and "__pycache__" not in str(p):
                replay_artifacts[str(p.relative_to(out_dir))] = p.read_bytes()
    replay_artifacts["schema_map.frozen.json"] = (out_dir / "schema_map.frozen.json").read_bytes()

    assert set(none_artifacts.keys()) == set(replay_artifacts.keys())
    for rel_path, content in none_artifacts.items():
        assert content == replay_artifacts[rel_path], (
            f"Core artifact {rel_path} differed between none and replay"
        )
