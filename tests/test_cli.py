"""
Unit tests for Typer CLI commands.
"""

from pathlib import Path
from typer.testing import CliRunner

from afm.cli import app

runner = CliRunner()


def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "AI Failure Museum" in result.output
    assert "reproduce" in result.output
    assert "evaluate" in result.output


def test_cli_list():
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "SYN-0001" in result.output
    assert "Synthetic" in result.output


def test_cli_list_json():
    result = runner.invoke(app, ["list", "--format", "json"])
    assert result.exit_code == 0
    assert '"id": "SYN-0001"' in result.output


def test_cli_show():
    result = runner.invoke(app, ["show", "SYN-0001"])
    assert result.exit_code == 0
    assert "Synthetic: Agent Invokes" in result.output
    assert "reproducible" in result.output


def test_cli_validate_all():
    result = runner.invoke(app, ["validate"])
    assert result.exit_code == 0
    assert "PASS" in result.output
    assert "All validated cases conform to specification" in result.output


def test_cli_doctor():
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "System Diagnostics" in result.output
    assert "Python Runtime" in result.output


def test_cli_report():
    result = runner.invoke(app, ["report", "SYN-0001"])
    assert result.exit_code == 0
    assert "# [SYN-0001]" in result.output
    assert "## Reproduction Procedure" in result.output


def test_cli_evaluate():
    result = runner.invoke(app, ["evaluate", "SYN-0001", "--adapter", "mock"])
    assert result.exit_code == 0
    assert "Agent Evaluation Report: SYN-0001" in result.output
    assert "mock (MOCK DOUBLE)" in result.output


def test_cli_reproduce_docker_safe_error():
    result = runner.invoke(app, ["reproduce", "SYN-0001"])
    # If Docker is not installed on host, must exit code 2 with safety warning
    assert result.exit_code in (0, 2)
    if result.exit_code == 2:
        assert "Reproduction Cannot Proceed" in result.output or "Docker is not available" in result.output
