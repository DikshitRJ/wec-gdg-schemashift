"""Output guard: parse, validate, and redact LLM outputs.

Spec: llm-assist/guard
"""

from __future__ import annotations

import json
import re
from typing import TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)


def redact_prompt(text: str) -> str:
    """Redact connection URIs and credentials from prompts."""
    # Redact mongodb URIs
    s = re.sub(r"mongodb://[^@]+@", "mongodb://<redacted>@", text)
    # Redact postgres URIs
    s = re.sub(r"postgresql://[^@]+@", "postgresql://<redacted>@", s)
    # Redact api keys
    s = re.sub(
        r"(api[_-]?key|password)\s*[:=]\s*['\"][^'\"]+['\"]", r"\1: '<redacted>'", s, flags=re.I
    )
    return s


def parse_and_validate[T: BaseModel](raw_text: str, target_model: type[T]) -> T | None:
    """Extract JSON from raw text and validate against target Pydantic model."""
    if not raw_text:
        return None

    cleaned = raw_text.strip()
    # Strip markdown code blocks if present
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    try:
        data = json.loads(cleaned)
    except Exception:
        # Try finding json block
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
            except Exception:
                return None
        else:
            return None

    try:
        return target_model.model_validate(data)
    except ValidationError:
        return None
