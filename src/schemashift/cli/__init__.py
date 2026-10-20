"""CLI package re-exports.

Spec: cli-tui/init
"""

from schemashift.cli.app import app
from schemashift.cli.tui import console, render_similarity_table

__all__ = ["app", "console", "render_similarity_table"]
