"""Tests for the CLI interface."""

import tempfile
from pathlib import Path

from click.testing import CliRunner

from prompteval.cli import main


def test_version():
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_help():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Prompt evaluation" in result.output


def test_init_creates_files():
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        result = runner.invoke(main, ["init", "--dir", tmpdir])
        assert result.exit_code == 0
        assert (Path(tmpdir) / "config.yaml").exists()
        assert (Path(tmpdir) / "prompts" / "summarize.yaml").exists()
        assert (Path(tmpdir) / "datasets" / "articles.yaml").exists()
        assert "scaffolded" in result.output.lower()


def test_init_skips_existing():
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        # First run creates files
        runner.invoke(main, ["init", "--dir", tmpdir])
        # Second run skips them
        result = runner.invoke(main, ["init", "--dir", tmpdir])
        assert result.exit_code == 0
        assert "skipped" in result.output.lower()


def test_run_missing_config():
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        result = runner.invoke(main, ["run", "--config", f"{tmpdir}/nonexistent.yaml"])
        assert result.exit_code != 0
        assert "not found" in result.output.lower()
