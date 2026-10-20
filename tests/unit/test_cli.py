"""Unit tests for CLI commands.

Spec: cli-tui/unit-test
"""

from typer.testing import CliRunner

from schemashift.cli.app import app

runner = CliRunner()


def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Hybrid MongoDB-to-PostgreSQL migration tool" in result.output
    assert "seed" in result.output
    assert "run" in result.output
    assert "inspect" in result.output
    assert "report" in result.output
