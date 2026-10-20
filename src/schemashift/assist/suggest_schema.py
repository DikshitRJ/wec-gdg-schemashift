"""Propose naming and relation refinements from source profile.

Spec: llm-assist/suggest-schema
"""

from __future__ import annotations

import json

from schemashift.assist.fallbacks import fallback_schema_proposal
from schemashift.contracts.llm import SchemaProposal
from schemashift.contracts.profile import SourceProfile
from schemashift.llm.client import LLMClient


def suggest_schema(
    profile: SourceProfile,
    llm_client: LLMClient,
) -> SchemaProposal:
    """Ask LLM to suggest naming or relational improvements."""
    # Build compact representation of profile
    summary = {
        "database": profile.database,
        "collections": [
            {
                "name": c.name,
                "fields": [f.path for f in c.fields[:15]],
            }
            for c in profile.collections
        ],
    }

    prompt = (
        "Given the following MongoDB collections and fields, propose SQL table or column name cleanups if appropriate.\n"
        f"Data: {json.dumps(summary)}\n"
        "Return SchemaProposal JSON with a list of proposals."
    )

    result = llm_client.complete(prompt, SchemaProposal)
    return result if result is not None else fallback_schema_proposal()
