"""Rich terminal UI formatting and display components.

Spec: cli-tui/tui
"""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from schemashift.contracts.similarity import Band, SimilarityReport

console = Console()


def render_node_badge(node_name: str, node_type: str = "D") -> None:
    """Print an execution badge for current pipeline node."""
    if node_type == "D":
        badge = "[bold white on blue] D (Deterministic) [/]"
    else:
        badge = "[bold white on magenta] ND (Assist) [/]"
    console.print(f"{badge} [bold cyan]Executing:[/] [yellow]{node_name}[/]")


def render_similarity_table(report: SimilarityReport) -> None:
    """Display Rich table for database schema similarity."""
    band_colors = {
        Band.MATCHED: "green",
        Band.GUESSED: "yellow",
        Band.NEEDS_REVIEW: "red",
    }
    color = band_colors.get(report.overall_band, "white")

    console.print()
    console.print(
        Panel(
            f"[bold]Overall Schema Match:[/] [{color}]{report.overall_score * 100:.1f}%[/] "
            f"([{color}]{report.overall_band.value.upper()}[/])\n"
            f"[dim]Matched: {report.matched_fields} | Guessed: {report.guessed_fields} | Needs Review: {report.needs_review_fields}[/]",
            title="[bold cyan]Database Similarity Assessment[/]",
            border_style=color,
        )
    )

    table = Table(title="Entity Breakdown", show_header=True, header_style="bold magenta")
    table.add_column("Collection", style="cyan")
    table.add_column("Target Tables", style="blue")
    table.add_column("Match %", justify="right")
    table.add_column("Fields", justify="right")
    table.add_column("Status", justify="center")

    for es in report.entity_scores:
        score_pct = f"{es.total * 100:.1f}%"
        status = (
            "[green]Matched[/]"
            if es.total >= 0.85
            else ("[yellow]Guessed[/]" if es.total >= 0.60 else "[red]Review[/]")
        )
        table.add_row(
            es.collection,
            ", ".join(es.tables) or "unmapped",
            score_pct,
            str(es.field_count),
            status,
        )

    console.print(table)

    if report.drag_list:
        drag_table = Table(title="Top Divergent / Ambiguous Fields", header_style="bold red")
        drag_table.add_column("Source Field", style="yellow")
        drag_table.add_column("Target", style="cyan")
        drag_table.add_column("Score", justify="right")
        drag_table.add_column("Reasons", style="dim")

        for fs in report.drag_list[:5]:
            tgt = f"{fs.target_table}.{fs.target_column}" if fs.target_table else "unmapped"
            drag_table.add_row(
                fs.source_path,
                tgt,
                f"{fs.total * 100:.1f}%",
                ", ".join(fs.reason_codes),
            )
        console.print(drag_table)
    console.print()


def render_gate_panel(items: list[dict], overall_score: float, overall_band: str) -> None:
    """Render human-in-the-loop gate review panel."""
    console.print()
    content = [
        "[bold yellow]HUMAN APPROVAL GATE REQUIRED[/]",
        f"Overall Match: [bold]{overall_score * 100:.1f}%[/] ({overall_band.upper()})",
        "",
        "The following mappings require explicit operator approval before freezing:",
    ]
    for it in items:
        content.append(f"- [bold red]{it.get('target')}[/]: {', '.join(it.get('reasons', []))}")

    content.append(
        "\n[bold]Options:[/] [green](a)pprove[/] | [red](r)eject[/] | [cyan](e)dit to overrides[/]"
    )

    console.print(Panel("\n".join(content), title="[bold red]Approval Gate[/]", border_style="red"))
