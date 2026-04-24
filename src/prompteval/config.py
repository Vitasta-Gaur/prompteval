"""Configuration loading and project scaffolding."""

import logging
import os
import re
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path

import click
import yaml

logger = logging.getLogger(__name__)


@dataclass
class ProviderConfig:
    api_key: str = ""
    models: list[str] = field(default_factory=list)
    base_url: str = ""


@dataclass
class EvaluationConfig:
    workers: int = 4
    timeout: int = 60
    prompts_dir: str = "prompts/"
    datasets_dir: str = "datasets/"


@dataclass
class SecurityConfig:
    enabled: bool = True
    injection: bool = True
    pii_detection: bool = True
    jailbreak: bool = True


@dataclass
class ScoringConfig:
    judge_provider: str = "anthropic"
    judge_model: str = "claude-sonnet-4-20250514"


@dataclass
class Config:
    providers: dict[str, ProviderConfig] = field(default_factory=dict)
    evaluation: EvaluationConfig = field(default_factory=EvaluationConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    scoring: ScoringConfig = field(default_factory=ScoringConfig)

    def active_providers(self) -> dict[str, ProviderConfig]:
        """Return providers that have API keys or are local (ollama)."""
        return {
            name: p for name, p in self.providers.items()
            if p.api_key or name == "ollama"
        }


def _resolve_env_vars(value):
    """Recursively resolve ${ENV_VAR} placeholders in strings."""
    if isinstance(value, str):
        def _replace(m):
            var_name = m.group(1)
            resolved = os.environ.get(var_name, "")
            if not resolved:
                logger.warning(f"Environment variable '{var_name}' is not set or empty")
            return resolved
        return re.sub(r"\$\{(\w+)\}", _replace, value)
    if isinstance(value, dict):
        return {k: _resolve_env_vars(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_env_vars(v) for v in value]
    return value


def _validate_config(config: Config):
    """Validate config values and raise on invalid settings."""
    if config.evaluation.workers < 1:
        raise click.ClickException(
            f"Invalid config: evaluation.workers must be >= 1, got {config.evaluation.workers}"
        )
    if config.evaluation.timeout < 1:
        raise click.ClickException(
            f"Invalid config: evaluation.timeout must be >= 1, got {config.evaluation.timeout}"
        )
    if not config.scoring.judge_provider:
        raise click.ClickException("Invalid config: scoring.judge_provider must not be empty")
    if not config.scoring.judge_model:
        raise click.ClickException("Invalid config: scoring.judge_model must not be empty")


def load_config(path: str) -> Config:
    """Load config from YAML or JSON file."""
    filepath = Path(path)
    if not filepath.exists():
        raise click.ClickException(f"Config file not found: {path}\nRun 'prompteval init' first.")

    raw = filepath.read_text()

    if filepath.suffix in (".yaml", ".yml"):
        data = yaml.safe_load(raw)
    else:
        import json
        data = json.loads(raw)

    data = _resolve_env_vars(data)

    # Build config
    providers = {}
    for name, pconf in data.get("providers", {}).items():
        providers[name] = ProviderConfig(
            api_key=pconf.get("api_key", ""),
            models=pconf.get("models", []),
            base_url=pconf.get("base_url", ""),
        )

    eval_data = data.get("evaluation", {})
    evaluation = EvaluationConfig(
        workers=eval_data.get("workers", 4),
        timeout=eval_data.get("timeout", 60),
        prompts_dir=eval_data.get("prompts_dir", "prompts/"),
        datasets_dir=eval_data.get("datasets_dir", "datasets/"),
    )

    sec_data = data.get("security", {})
    security = SecurityConfig(
        injection=sec_data.get("injection", True),
        pii_detection=sec_data.get("pii_detection", True),
        jailbreak=sec_data.get("jailbreak", True),
    )

    score_data = data.get("scoring", {})
    scoring = ScoringConfig(
        judge_provider=score_data.get("judge_provider", "anthropic"),
        judge_model=score_data.get("judge_model", "claude-sonnet-4-20250514"),
    )

    config = Config(providers=providers, evaluation=evaluation, security=security, scoring=scoring)
    _validate_config(config)
    return config


def scaffold_project(target_dir: str):
    """Create config, prompts, and datasets directories with sample files."""
    target = Path(target_dir)
    target.mkdir(parents=True, exist_ok=True)

    templates_pkg = resources.files("prompteval") / "templates"

    files_to_copy = {
        "config.yaml": target / "config.yaml",
        "sample_prompt.yaml": target / "prompts" / "summarize.yaml",
        "sample_dataset.yaml": target / "datasets" / "articles.yaml",
    }

    for template_name, dest in files_to_copy.items():
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            click.echo(f"  Skipped (exists): {dest}")
            continue
        content = (templates_pkg / template_name).read_text()
        dest.write_text(content)
        click.echo(f"  Created: {dest}")

    click.echo("\nProject scaffolded! Next steps:")
    click.echo("  1. Edit config.yaml with your API keys")
    click.echo("  2. Add prompts to prompts/")
    click.echo("  3. Add datasets to datasets/")
    click.echo("  4. Run: prompteval run")
