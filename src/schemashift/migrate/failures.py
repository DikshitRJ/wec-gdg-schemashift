"""Row-level migration failures and reporting.

Spec: migrate/failures
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field


class RowFailure(BaseModel):
    """Details of a single row or field failure during ETL load."""

    collection: str
    doc_id: str
    path: str
    column: str
    value_repr: str
    reason: str
    hint: str = ""


def write_failures_report(
    failures: list[RowFailure],
    out_dir: str | Path,
) -> str:
    """Save row failures to <out_dir>/reports/failures.json."""
    p = Path(out_dir) / "reports" / "failures.json"
    p.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "total_failures": len(failures),
        "failures": [f.model_dump() for f in failures],
    }
    p.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(p.resolve())
