"""Tests for report generation."""

import tempfile
from pathlib import Path

from prompteval.config import Config
from prompteval.evaluator import EvalResult
from prompteval.providers.base import LLMResponse
from prompteval.security.pii import SecurityFinding
from prompteval.report.generator import (
    generate_report,
    _build_summary,
    _build_quality_table,
)


def _make_result(provider="anthropic", model="claude", score=8.0, error=None):
    response = None
    if not error:
        response = LLMResponse(
            text="Test response",
            input_tokens=100,
            output_tokens=50,
            latency_ms=500.0,
            model=model,
            provider=provider,
        )
    return EvalResult(
        prompt_name="test-prompt",
        dataset_name="test-data",
        row_index=0,
        provider=provider,
        model=model,
        rendered_prompt="Test prompt",
        response=response,
        quality_score=score if not error else None,
        estimated_cost=0.005,
        error=error,
    )


def test_build_summary():
    results = [_make_result(), _make_result(score=6.0), _make_result(error="timeout")]
    findings = [SecurityFinding("pii", "high", "test", "evidence")]
    summary = _build_summary(results, findings)

    assert summary["total_runs"] == 3
    assert summary["successful"] == 2
    assert summary["errors"] == 1
    assert summary["security_issues"] == 1
    assert summary["avg_quality_score"] == 7.0


def test_build_quality_table():
    results = [
        _make_result(provider="anthropic", model="claude", score=8.0),
        _make_result(provider="anthropic", model="claude", score=9.0),
        _make_result(provider="openai", model="gpt-4o", score=7.0),
    ]
    rows = _build_quality_table(results)
    assert len(rows) == 2  # two provider/model combos
    claude_row = next(r for r in rows if r["provider"] == "anthropic")
    assert claude_row["avg_score"] == 8.5
    assert claude_row["runs"] == 2


def test_generate_report_creates_file():
    results = [_make_result(), _make_result(error="timeout")]
    findings = [SecurityFinding("pii", "medium", "Email found", "test@example.com")]
    config = Config()

    with tempfile.TemporaryDirectory() as tmpdir:
        output = str(Path(tmpdir) / "report.html")
        generate_report(results, findings, config, output)

        html = Path(output).read_text()
        assert "PromptEval Report" in html
        assert "test-prompt" in html
        assert "Email found" in html


def test_generate_report_empty_results():
    config = Config()
    with tempfile.TemporaryDirectory() as tmpdir:
        output = str(Path(tmpdir) / "report.html")
        generate_report([], [], config, output)

        html = Path(output).read_text()
        assert "PromptEval Report" in html
        assert "No security issues found" in html
