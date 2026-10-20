"""Interactive terminal approval prompts for HITL gates.

Spec: cli-tui/prompts
"""

from __future__ import annotations

from rich.prompt import Prompt


def prompt_approval(items: list[dict]) -> tuple[str, list[dict]]:
    """Prompt user for gate approval, rejection, or overrides.

    Returns (action, overrides_list).
    """
    choice = Prompt.ask(
        "[bold]Decision[/]",
        choices=["a", "r", "e", "approve", "reject", "edit"],
        default="a",
    ).lower()

    if choice in ("a", "approve"):
        return "approve", []
    elif choice in ("r", "reject"):
        return "reject", []
    else:
        # Edit overrides
        target = Prompt.ask("Enter target field to override (e.g. reviews.rating)")
        pg_type = Prompt.ask("Enter target PostgreSQL type", default="TEXT")
        transform = Prompt.ask("Enter transform name", default="identity")
        overrides = [
            {
                "target": target,
                "set": {
                    "pg_type": pg_type,
                    "transform": transform,
                },
            }
        ]
        return "approve", overrides
