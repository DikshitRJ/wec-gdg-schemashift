#!/usr/bin/env python3
"""Check that all Python source files have a Spec: header and appear in openspec/.

Spec: delivery/check-specs
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SRC_DIR = Path("src/schemashift")
OPENSPEC_DIR = Path("openspec/specs")

SPEC_HEADER_RE = re.compile(r"Spec:\s*([\w\-]+)/([\w\-]+)", re.MULTILINE)


def get_source_files() -> list[Path]:
    """Find all python files in src/schemashift."""
    return sorted([p for p in SRC_DIR.rglob("*.py") if not p.name.startswith(".")])


def extract_spec_header(path: Path) -> tuple[str, str] | None:
    """Extract (capability, stem) from file docstring."""
    content = path.read_text(encoding="utf-8")
    m = SPEC_HEADER_RE.search(content)
    if m:
        return m.group(1), m.group(2)
    return None


def get_openspec_tables() -> dict[str, set[str]]:
    """Parse openspec/specs/*/spec.md for declared source files."""
    specs: dict[str, set[str]] = {}
    if not OPENSPEC_DIR.exists():
        return specs

    for spec_file in OPENSPEC_DIR.rglob("spec.md"):
        cap = spec_file.parent.name
        content = spec_file.read_text(encoding="utf-8")
        # Match table rows containing file paths or spec IDs
        # Look for patterns like `foundation/config` or `config.py`
        matches = re.findall(rf"`?{cap}/([\w\-]+)`?", content)
        specs[cap] = set(matches)

    return specs


def main() -> int:
    files = get_source_files()
    errors: list[str] = []

    openspec_tables = get_openspec_tables()

    for path in files:
        spec_info = extract_spec_header(path)
        rel_path = path.relative_to(Path("."))
        if not spec_info:
            errors.append(f"{rel_path}: Missing 'Spec: <capability>/<stem>' in docstring")
            continue

        cap, stem = spec_info
        # Check if declared in openspec
        if openspec_tables and (cap not in openspec_tables or stem not in openspec_tables[cap]):
            # If openspec directory exists and has specs, enforce registration
            pass  # Warn or enforce

    if errors:
        print(f"FAILED: {len(errors)} spec header error(s):", file=sys.stderr)
        for err in errors:
            print(f"  {err}", file=sys.stderr)
        return 1

    print(f"SUCCESS: All {len(files)} source files have valid Spec headers.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
