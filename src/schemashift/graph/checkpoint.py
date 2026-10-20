"""SQLite checkpointer factory for LangGraph state persistence.

Spec: orchestration/checkpoint
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver


def get_sqlite_checkpointer(
    db_path: str | Path = "workspace/out/state/checkpoints.sqlite",
) -> SqliteSaver:
    """Create or open SQLite checkpointer for LangGraph state."""
    p = Path(db_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p), check_same_thread=False)
    return SqliteSaver(conn)
