"""Typer CLI application entry point and commands.

Spec: cli-tui/app
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import typer

from schemashift.cli.prompts import prompt_approval
from schemashift.cli.tui import (
    console,
    render_gate_panel,
    render_node_badge,
    render_similarity_table,
)
from schemashift.config import Settings
from schemashift.contracts.similarity import SimilarityReport
from schemashift.errors import (
    ConfigurationError,
    GateRejectedError,
    MigrationError,
    VerificationError,
)
from schemashift.graph.runner import MigrationRunner

app = typer.Typer(
    name="schemashift",
    help="Hybrid MongoDB-to-PostgreSQL migration tool.",
    no_args_is_help=True,
)


@app.command()
def seed(
    uri: str = typer.Option("mongodb://localhost:27017", help="MongoDB connection URI"),
    db: str = typer.Option("shop", help="Target database name"),
    inject: str | None = typer.Option(
        None, help="Inject failure flag (orphan_review, bad_date, uncoercible_rating)"
    ),
) -> None:
    """Seed MongoDB with realistic deterministic nested shop data."""
    from pymongo import MongoClient

    from schemashift.seed.shop import seed_shop

    inject_set = {inject} if inject else set()
    console.print(f"[bold cyan]Connecting to MongoDB at {uri} (db: {db})...[/]")
    client: MongoClient[dict[str, Any]] = MongoClient(uri)
    counts = seed_shop(client, db_name=db, inject=inject_set)
    console.print("[bold green]Deterministic seed complete:[/]")
    for coll, count in counts.items():
        console.print(f"  - {coll}: {count} documents")


@app.command()
def run(
    config: str = typer.Option("workspace/schemashift.yaml", help="Path to config file"),
    ci: bool = typer.Option(False, help="Run in non-interactive CI mode"),
    provider: str = typer.Option("none", help="LLM provider: none | replay | openai"),
    run_id: str | None = typer.Option(None, help="Custom execution run ID"),
) -> None:
    """Run full hybrid migration pipeline end-to-end."""
    runner = MigrationRunner()
    current_run_id = run_id

    try:
        stream = runner.run(
            config_path=config, ci_mode=ci, provider=provider, run_id=current_run_id
        )
        for update in stream:
            ev = update.get("event")
            if ev == "update":
                data = update.get("data", {})
                for node_name, node_val in data.items():
                    if isinstance(node_val, dict):
                        node_type = node_val.get("node_type", "D")
                        render_node_badge(node_name, node_type)

                        if node_name == "similarity_report" and "similarity_path" in node_val:
                            rep_path = Path(node_val["similarity_path"])
                            if rep_path.exists():
                                rep = SimilarityReport.model_validate(
                                    json.loads(rep_path.read_text(encoding="utf-8"))
                                )
                                render_similarity_table(rep)

            elif ev == "complete":
                update.get("state", {})
                current_run_id = update.get("run_id")

                # Check if paused at interrupt (gate)
                app_state = runner.app.get_state({"configurable": {"thread_id": current_run_id}})
                if app_state and app_state.next and not ci:
                    # Interactive prompt at gate
                    next_node = app_state.next[0]
                    if "approval_gate" in next_node or "gate" in next_node:
                        # Extract interrupt value
                        int_vals = app_state.tasks[0].interrupts if app_state.tasks else []
                        int_payload = int_vals[0].value if int_vals else {}
                        items = int_payload.get("items", [])
                        overall_score = int_payload.get("overall_score", 0.0)
                        overall_band = int_payload.get("overall_band", "needs_review")

                        render_gate_panel(items, overall_score, overall_band)
                        action, overrides = prompt_approval(items)

                        console.print(f"[bold cyan]Resuming pipeline with action={action}...[/]")
                        assert current_run_id is not None
                        resume_stream = runner.resume(
                            current_run_id, action=action, overrides=overrides
                        )
                        for r_update in resume_stream:
                            if r_update.get("event") == "update":
                                for r_node, r_val in r_update.get("data", {}).items():
                                    if isinstance(r_val, dict):
                                        render_node_badge(r_node, r_val.get("node_type", "D"))

        console.print("\n[bold green]SchemaShift pipeline completed successfully! (exit 0)[/]")
        sys.exit(0)

    except GateRejectedError as gre:
        console.print(f"\n[bold red]Pipeline halted: {gre}[/]")
        sys.exit(2)
    except VerificationError as ve:
        console.print(f"\n[bold red]Verification failed: {ve}[/]")
        sys.exit(3)
    except MigrationError as me:
        console.print(f"\n[bold red]Migration failed: {me}[/]")
        sys.exit(4)
    except ConfigurationError as ce:
        console.print(f"\n[bold red]Configuration error: {ce}[/]")
        sys.exit(5)
    except Exception as exc:
        console.print(f"\n[bold red]Unexpected error: {exc}[/]")
        sys.exit(6)


@app.command()
def demo() -> None:
    """Run full demonstration workflow in non-interactive replay mode."""
    run(config="workspace/schemashift.yaml", ci=True, provider="replay", run_id="demo-run")


@app.command()
def inspect(
    config: str = typer.Option("workspace/schemashift.yaml", help="Path to config file"),
) -> None:
    """Inspect and profile MongoDB source database."""
    from pymongo import MongoClient

    from schemashift.inspection.profile import build_profile, write_profile

    settings = Settings.load(config)
    client: MongoClient[dict[str, Any]] = MongoClient(settings.source.uri)
    prof = build_profile(client, settings.source.database, settings.sampling.size)
    path = write_profile(prof, settings.paths.out)
    console.print(f"[bold green]Inspection profile written to:[/] {path}")


@app.command()
def report(
    config: str = typer.Option("workspace/schemashift.yaml", help="Path to config file"),
) -> None:
    """Display latest schema similarity report."""
    settings = Settings.load(config)
    path = Path(settings.paths.out) / "reports" / "similarity.json"
    if not path.exists():
        console.print("[red]No similarity report found. Run inspection first.[/]")
        sys.exit(5)
    rep = SimilarityReport.model_validate(json.loads(path.read_text(encoding="utf-8")))
    render_similarity_table(rep)


@app.command()
def rollback(
    config: str = typer.Option("workspace/schemashift.yaml", help="Path to config file"),
) -> None:
    """Execute rollback script to drop target SQL tables."""
    from schemashift.migrate.executor import execute_sql_script

    settings = Settings.load(config)
    path = Path(settings.paths.out) / "migrations" / "001_schema.down.sql"
    if not path.exists():
        console.print("[red]Rollback script not found. Run generate first.[/]")
        sys.exit(5)
    sql = path.read_text(encoding="utf-8")
    execute_sql_script(settings.target.uri, sql, stop_on_error=False)
    console.print("[bold green]Rollback completed: target tables dropped.[/]")


if __name__ == "__main__":
    app()
