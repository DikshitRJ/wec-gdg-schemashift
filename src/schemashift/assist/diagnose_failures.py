"""Diagnose row-level migration failures and suggest remap patches.

Spec: llm-assist/diagnose-failures
"""

from __future__ import annotations

import json

from schemashift.assist.fallbacks import fallback_diagnose_failures
from schemashift.contracts.llm import RemapPatch
from schemashift.llm.client import LLMClient
from schemashift.migrate.failures import RowFailure


def diagnose_failures(
    failures: list[RowFailure],
    llm_client: LLMClient,
) -> RemapPatch:
    """Analyze row failures and propose a remap patch for human approval."""
    if not failures:
        return fallback_diagnose_failures(failures)

    summary = [
        {
            "collection": f.collection,
            "column": f.column,
            "path": f.path,
            "value": f.value_repr,
            "reason": f.reason,
        }
        for f in failures[:5]
    ]

    prompt = (
        "The following rows failed during ETL migration:\n"
        f"{json.dumps(summary, indent=2)}\n"
        "Propose a RemapPatch JSON with target (e.g. 'reviews.rating'), changes (e.g. {'pg_type': 'TEXT'}), and rationale."
    )

    patch = llm_client.complete(prompt, RemapPatch)
    if not patch or not patch.target:
        patch = fallback_diagnose_failures(failures)
    return patch
