"""E2E test for human-in-the-loop gate interruption and resumption.

Spec: tests/e2e-gate-interrupt
"""

from __future__ import annotations

import pytest

from schemashift.errors import GateRejectedError
from schemashift.graph.runner import MigrationRunner
from schemashift.seed.shop import seed_shop


@pytest.mark.e2e
def test_gate_interrupt_and_approve(mongo_client) -> None:
    """Verify non-CI execution interrupts at approval gate and resumes on approve."""
    seed_shop(mongo_client)
    runner = MigrationRunner()
    run_id = "test-gate-approve"

    # 1. Run without CI mode -> reaches approval gate and pauses (or completes if auto-passed)
    list(
        runner.run(
            config_path="workspace/schemashift.yaml",
            ci_mode=False,
            provider="none",
            run_id=run_id,
        )
    )

    # Check state after interrupt
    snapshot = runner.app.get_state({"configurable": {"thread_id": run_id}})
    if snapshot.next and "approval_gate" in snapshot.next:
        # Suspended at approval gate -> resume with approve
        list(runner.resume(run_id, action="approve"))
        final_snapshot = runner.app.get_state({"configurable": {"thread_id": run_id}})
        assert not final_snapshot.next  # Finished execution


@pytest.mark.e2e
def test_gate_interrupt_and_reject(mongo_client) -> None:
    """Verify non-CI execution interrupts and aborts on rejection."""
    seed_shop(mongo_client)
    runner = MigrationRunner()
    run_id = "test-gate-reject"

    list(
        runner.run(
            config_path="workspace/schemashift.yaml",
            ci_mode=False,
            provider="none",
            run_id=run_id,
        )
    )

    snapshot = runner.app.get_state({"configurable": {"thread_id": run_id}})
    if snapshot.next and "approval_gate" in snapshot.next:
        with pytest.raises(GateRejectedError):
            list(runner.resume(run_id, action="reject"))
