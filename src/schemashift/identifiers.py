"""SQL identifier utilities: quoting, snake-casing, safe naming.

Spec: foundation/identifiers
"""

from __future__ import annotations

import re
import unicodedata

_MAX_IDENT_LEN = 63  # PostgreSQL limit


def quote_ident(name: str) -> str:
    """Quote a PostgreSQL identifier, escaping embedded double-quotes."""
    safe = name.replace('"', '""')
    return f'"{safe}"'


def snake_case(name: str) -> str:
    """Convert camelCase / PascalCase / kebab-case to snake_case."""
    # Insert _ before uppercase runs
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s)
    s = s.replace("-", "_").replace(" ", "_")
    return s.lower()


def safe_name(name: str, *, max_len: int = _MAX_IDENT_LEN) -> str:
    """Produce a safe, lowercase, underscore-separated SQL identifier.

    Strips non-ASCII, leading digits, collapses underscores, truncates.
    """
    # Normalize unicode
    n = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    n = snake_case(n)
    # Keep only alnum and underscore
    n = re.sub(r"[^a-z0-9_]", "_", n)
    n = re.sub(r"_+", "_", n).strip("_")
    # No leading digit
    if n and n[0].isdigit():
        n = f"col_{n}"
    # Truncate
    if len(n) > max_len:
        n = n[:max_len].rstrip("_")
    return n or "unnamed"


def pluralize(name: str) -> str:
    """Simple English pluralization for table names."""
    if name.endswith("s"):
        return name
    if name.endswith("y") and len(name) > 1 and name[-2] not in "aeiou":
        return name[:-1] + "ies"
    if name.endswith(("ch", "sh", "x", "z")):
        return name + "es"
    return name + "s"


def singularize(name: str) -> str:
    """Simple English singularization."""
    if name.endswith("ies") and len(name) > 3:
        return name[:-3] + "y"
    if name.endswith("ses") or name.endswith("xes") or name.endswith("zes"):
        return name[:-2]
    if name.endswith("ches") or name.endswith("shes"):
        return name[:-2]
    if name.endswith("s") and not name.endswith("ss"):
        return name[:-1]
    return name
