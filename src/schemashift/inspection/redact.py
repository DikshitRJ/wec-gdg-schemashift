"""Example-value redaction for LLM safety.

Keeps at most 3 examples per field, hashes strings longer than 20
characters, and truncates everything beyond 50 characters.

Spec: inspection/redact
"""

from __future__ import annotations

import hashlib
from typing import Any

from schemashift.contracts.profile import FieldProfile

_MAX_EXAMPLES = 3
_HASH_THRESHOLD = 20
_TRUNCATE_LIMIT = 50


def _redact_value(value: Any) -> Any:
    """Return a redacted copy of *value*.

    * Strings longer than ``_HASH_THRESHOLD`` chars are replaced by a
      SHA-256 prefix (``hash:<12 hex chars>``).
    * Any string representation exceeding ``_TRUNCATE_LIMIT`` chars is
      truncated with an ellipsis.
    * Dicts and lists are processed recursively.
    * All other scalars pass through unchanged.
    """
    if isinstance(value, str):
        if len(value) > _HASH_THRESHOLD:
            digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]
            return f"hash:{digest}"
        if len(value) > _TRUNCATE_LIMIT:
            return value[:_TRUNCATE_LIMIT] + "…"
        return value

    if isinstance(value, dict):
        return {k: _redact_value(v) for k, v in sorted(value.items())}

    if isinstance(value, list):
        return [_redact_value(item) for item in value]

    if value is None or isinstance(value, (int, float, bool)):
        return value

    # Scalars (ObjectId, Decimal, Decimal128, datetime, etc.).
    text = str(value)
    if len(text) > _TRUNCATE_LIMIT:
        return text[:_TRUNCATE_LIMIT] + "…"
    return text


def redact_examples(field: FieldProfile) -> FieldProfile:
    """Return a copy of *field* with redacted and capped examples.

    Parameters
    ----------
    field:
        A ``FieldProfile`` whose ``examples`` may contain raw values.

    Returns
    -------
    FieldProfile
        A new ``FieldProfile`` with at most ``_MAX_EXAMPLES`` entries,
        each individually redacted.
    """
    redacted = [_redact_value(ex) for ex in field.examples[:_MAX_EXAMPLES]]
    return field.model_copy(update={"examples": redacted})
