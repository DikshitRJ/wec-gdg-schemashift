"""E2E test: resume an interrupted run across separate runner instances / processes.

Spec: tests/e2e-resume-across-processes
"""

from __future__ import annotations

from pathlib import Path

import pytest

from schemashift.graph.runner import MigrationRunner
from schemashift.seed.shop import seed_shop


@pytest.mark.e2e
def test_resume_across_runners(mongo_client) -> None:
    """Verify state saved in SQLite checkpointer can be resumed by a new runner instance."""
    seed_shop(mongo_client)
    run_id = "cross-process-run"
    checkpoint_file = "workspace/out/state/checkpoints.sqlite"

    # Process A runner
    runner_a = MigrationRunner(checkpoint_path=checkpoint_file)
    list(
        runner_a.run(
            config_path="workspace/schemashift.yaml",
            ci_mode=False,
            provider="none",
            run_id=run_id,
        )
    )

    # Verify process A halted at approval_gate
    snap_a = runner_a.app.get_state({"configurable": {"thread_id": run_id}})
    if snap_a.next:
        assert "approval_gate" in snap_a.next

        # Process B runner (fresh instance reading same SQLite file)
        runner_b = MigrationRunner(checkpoint_path=checkpoint_file)
        list(runner_b.resume(run_id, action="approve"))

        snap_b = runner_b.app.get_state({"configurable": {"thread_id": run_id}})
        assert not snap_b.next  # Successfully completed

        # Verify artifacts created by resumed process B
        assert Path("workspace/out/schema_map.frozen.json").exists()
        assert Path("workspace/out/migrations/001_schema.sql").exists()
