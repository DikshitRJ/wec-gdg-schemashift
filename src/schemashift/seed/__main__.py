"""CLI entry-point: ``python -m schemashift.seed``.

Spec: seed/main
"""

from __future__ import annotations

import argparse
import sys

from pymongo import MongoClient

from schemashift.errors import SchemaShiftError
from schemashift.seed.shop import seed_shop


def _build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the seed CLI."""
    parser = argparse.ArgumentParser(
        prog="python -m schemashift.seed",
        description="Seed a MongoDB 'shop' database with deterministic test data.",
    )
    parser.add_argument(
        "--uri",
        default="mongodb://localhost:27017",
        help="MongoDB connection URI (default: mongodb://localhost:27017)",
    )
    parser.add_argument(
        "--inject",
        action="append",
        choices=["orphan_review", "bad_date", "uncoercible_rating"],
        default=None,
        help=(
            "Inject a data-quality anomaly.  May be repeated. "
            "Choices: orphan_review, bad_date, uncoercible_rating"
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    """Parse CLI arguments and run the seed function."""
    args = _build_parser().parse_args(argv)

    inject: set[str] = set(args.inject) if args.inject else set()

    try:
        client: MongoClient = MongoClient(args.uri)
        # Quick connectivity check
        client.admin.command("ping")
    except Exception as exc:
        raise SchemaShiftError(
            f"Cannot connect to MongoDB at {args.uri}: {exc}",
            hint="Ensure mongod is running and the URI is correct.",
        ) from exc

    counts = seed_shop(client, inject=inject)

    print("Seeded 'shop' database:")
    for name in sorted(counts):
        print(f"  {name}: {counts[name]} documents")

    if inject:
        print(f"Injected anomalies: {', '.join(sorted(inject))}")


if __name__ == "__main__":
    try:
        main()
    except SchemaShiftError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        if exc.hint:
            print(f"HINT:  {exc.hint}", file=sys.stderr)
        sys.exit(exc.exit_code)
