"""Suggest query idioms and refactor notes for the generated ORM layer.

Spec: llm-assist/refactor-notes
"""

from __future__ import annotations

from pathlib import Path

from schemashift.contracts.llm import RefactorNote
from schemashift.contracts.schema_map import SchemaMap
from schemashift.llm.client import LLMClient


def generate_refactor_notes(
    schema_map: SchemaMap,
    llm_client: LLMClient,
    out_dir: str | Path = "workspace/out",
) -> str:
    """Generate refactoring guidance and update orm/REFACTOR_NOTES.md."""
    prompt = (
        f"Review this target schema: {[t.name for t in schema_map.tables]}.\n"
        "Suggest query idioms for replacing MongoDB queries (like $lookup or nested filters) with SQLAlchemy."
    )
    note = llm_client.complete(prompt, RefactorNote)
    text = (
        note.suggestion
        if note and note.suggestion
        else "Use SQLAlchemy session queries and repository methods for basic CRUD."
    )

    p = Path(out_dir) / "orm" / "REFACTOR_NOTES.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    existing = p.read_text(encoding="utf-8") if p.exists() else ""
    updated = f"{existing}\n\n## Assisted Query Refactor Guidance\n\n{text}\n"
    p.write_text(updated, encoding="utf-8")
    return text
