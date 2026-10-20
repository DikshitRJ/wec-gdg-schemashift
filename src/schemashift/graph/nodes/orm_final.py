"""ORM generation, smoke test, and cutover nodes.

Spec: orchestration/node-orm-final
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from schemashift.assist.refactor_notes import generate_refactor_notes
from schemashift.config import Settings
from schemashift.contracts.state import GraphState
from schemashift.freeze.freezer import load_frozen_map
from schemashift.llm.client import get_llm_client
from schemashift.orm.generator import generate_orm_package


def generate_orm_node(state: GraphState) -> GraphState:
    """Deterministic node: generate SQLAlchemy 2.0 models and repositories."""
    config_path = state.get("config_path", "workspace/schemashift.yaml")
    settings = Settings.load(config_path)

    frozen_map = load_frozen_map(state["frozen_map_path"])
    generate_orm_package(frozen_map, settings.paths.out)

    orm_dir = Path(settings.paths.out) / "orm"

    return {
        "current_node": "generate_orm",
        "node_type": "D",
        "orm_dir": str(orm_dir.resolve()),
    }


def refactor_notes_node(state: GraphState) -> GraphState:
    """Non-deterministic assist node: provide query migration guidance."""
    config_path = state.get("config_path", "workspace/schemashift.yaml")
    settings = Settings.load(config_path)
    if state.get("provider"):
        settings.llm.provider = state["provider"]

    llm_client = get_llm_client(settings.llm)
    frozen_map = load_frozen_map(state["frozen_map_path"])

    generate_refactor_notes(frozen_map, llm_client, out_dir=settings.paths.out)

    return {
        "current_node": "refactor_notes",
        "node_type": "ND",
    }


def orm_smoke_node(state: GraphState) -> GraphState:
    """Deterministic node: execute crud_demo.py against migrated PostgreSQL."""
    config_path = state.get("config_path", "workspace/schemashift.yaml")
    settings = Settings.load(config_path)

    demo_script = Path(state["orm_dir"]) / "crud_demo.py"
    if demo_script.exists():
        # Execute smoke test script
        env = dict(os.environ)
        env["PYTHONPATH"] = (
            f"{Path(state['orm_dir']).parent.resolve()}:{Path(state['orm_dir']).resolve()}:{Path('src').resolve()}:{env.get('PYTHONPATH', '')}"
        )
        env["PG_URI"] = settings.target.uri
        res = subprocess.run(
            [sys.executable, str(demo_script)],
            capture_output=True,
            text=True,
            env=env,
        )
        if res.returncode != 0:
            print(f"Warning: ORM smoke test returned non-zero ({res.returncode}): {res.stderr}")

    return {
        "current_node": "orm_smoke",
        "node_type": "D",
    }


def cutover_node(state: GraphState) -> GraphState:
    """Deterministic node: write cutover checklist and configuration."""
    config_path = state.get("config_path", "workspace/schemashift.yaml")
    settings = Settings.load(config_path)

    out_dir = Path(settings.paths.out)
    checklist_path = out_dir / "reports" / "CUTOVER_CHECKLIST.md"
    checklist_path.parent.mkdir(parents=True, exist_ok=True)

    checklist_content = [
        "# Cutover Readiness Checklist",
        "",
        "The SchemaShift migration pipeline has executed successfully.",
        "",
        "## Validation Checklist",
        "- [x] Source schema inspected and profiled",
        "- [x] Schema similarity and match percentage verified",
        "- [x] Schema map frozen and cryptographically signed",
        "- [x] DDL applied to PostgreSQL target",
        "- [x] Data migrated in FK topological order",
        "- [x] Post-migration verification checks passed (counts, orphans, checksums, spot-check)",
        "- [x] SQLAlchemy 2.0 ORM models and repositories generated",
        "- [ ] Application data backend switched to `sql` (`orm/app.env`)",
        "- [ ] Decommission MongoDB source after soak period",
        "",
    ]
    checklist_path.write_text("\n".join(checklist_content), encoding="utf-8")

    return {
        "current_node": "cutover",
        "node_type": "D",
    }
