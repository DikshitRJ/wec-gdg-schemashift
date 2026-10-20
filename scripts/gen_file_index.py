#!/usr/bin/env python3
"""Generate a file index with spec annotations for documentation.

Spec: scripts/gen-file-index
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def extract_spec(file_path: Path) -> str:
    """Extract 'Spec: ...' from file docstring."""
    try:
        content = file_path.read_text(encoding="utf-8")
        for line in content.splitlines():
            line_str = line.strip()
            if line_str.startswith("Spec:"):
                return line_str.replace("Spec:", "").strip()
            if "Spec:" in line_str:
                return line_str.split("Spec:")[-1].strip().rstrip("\"').*")
    except Exception:
        pass
    return ""


def main() -> None:
    print("# SchemaShift Codebase File Index\n")
    print("| Path | Spec | Description |")
    print("|---|---|---|")

    for dir_name in ["src", "tests", "scripts", "workspace", "examples"]:
        base_dir = ROOT / dir_name
        if not base_dir.exists():
            continue
        for path in sorted(base_dir.rglob("*")):
            if path.is_file() and "__pycache__" not in str(path) and not path.name.endswith(".pyc"):
                rel = path.relative_to(ROOT)
                spec = extract_spec(path)
                print(f"| `{rel}` | {spec or '-'} | - |")


if __name__ == "__main__":
    main()
