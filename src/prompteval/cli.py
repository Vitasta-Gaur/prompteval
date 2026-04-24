"""CLI entry point for prompteval."""

import click

from prompteval import __version__


@click.group()
@click.version_option(version=__version__)
def main():
    """Prompt evaluation and security auditing tool for LLMs."""
    pass


@main.command()
@click.option("--dir", "target_dir", default=".", help="Directory to scaffold into")
def init(target_dir):
    """Scaffold config, sample prompts, and datasets."""
    from prompteval.config import scaffold_project

    scaffold_project(target_dir)


@main.command()
@click.option("--config", "config_path", default="config.yaml", help="Path to config file")
@click.option("--output", default="report.html", help="Output report path")
@click.option("--security/--no-security", default=True, help="Run security audits")
@click.option("--workers", default=None, type=int, help="Parallel workers (overrides config)")
@click.option("-v", "--verbose", count=True, help="Increase verbosity (-v info, -vv debug)")
def run(config_path, output, security, workers, verbose):
    """Run evaluation and generate report."""
    import asyncio
    import logging

    from prompteval.config import load_config
    from prompteval.evaluator import run_evaluation
    from prompteval.report.generator import generate_report

    # Set up logging
    level = {0: logging.WARNING, 1: logging.INFO}.get(verbose, logging.DEBUG)
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")

    config = load_config(config_path)
    if workers is not None:
        config.evaluation.workers = workers
    config.security.enabled = security

    click.echo(f"Loaded config: {len(config.active_providers())} provider(s)")

    results, security_findings = asyncio.run(run_evaluation(config))

    click.echo(f"Completed {len(results)} evaluation(s)")
    if security_findings:
        click.echo(f"Found {len(security_findings)} security issue(s)")

    generate_report(results, security_findings, config, output)
    click.echo(f"Report saved to {output}")
