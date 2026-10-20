"""End-to-end happy path test running the full LangGraph pipeline via runner.

Spec: tests/e2e-happy-path
"""

import json
from pathlib import Path

import pytest

from schemashift.graph.runner import MigrationRunner
from schemashift.seed.shop import seed_shop


@pytest.mark.e2e
def test_happy_path_pipeline(mongo_client):
    # 1. Seed database
    seed_shop(mongo_client)

    # 2. Run full pipeline in CI mode with provider=none
    runner = MigrationRunner()
    stream = runner.run(
        config_path="workspace/schemashift.yaml",
        ci_mode=True,
        provider="none",
        run_id="e2e-happy-path",
    )

    for update in stream:
        if update.get("event") == "complete":
            update.get("state", {})

    # 3. Assert artifacts were created
    out_dir = Path("workspace/out")
    assert (out_dir / "reports" / "similarity.json").exists()
    assert (out_dir / "reports" / "verify.json").exists()
    assert (out_dir / "schema_map.frozen.json").exists()
    assert (out_dir / "migrations" / "001_schema.sql").exists()
    assert (out_dir / "etl" / "etl_plan.json").exists()
    assert (out_dir / "orm" / "models.py").exists()
    assert (out_dir / "orm" / "repositories.py").exists()

    # 4. Check verification report passed
    ver_data = json.loads((out_dir / "reports" / "verify.json").read_text(encoding="utf-8"))
    assert ver_data["passed"] is True
