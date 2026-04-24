"""Core evaluation engine."""

import asyncio
import logging
from dataclasses import dataclass, field
from pathlib import Path

import click
import yaml

from prompteval.config import Config
from prompteval.providers import get_provider
from prompteval.providers.base import BaseProvider, LLMResponse
from prompteval.scoring.cost import estimate_cost
from prompteval.scoring.quality import score_quality
from prompteval.security.pii import SecurityFinding, scan_for_pii
from prompteval.security.injection import run_injection_check
from prompteval.security.jailbreak import run_jailbreak_check

logger = logging.getLogger(__name__)


@dataclass
class PromptTemplate:
    name: str
    template: str
    variables: list[str]
    description: str = ""


@dataclass
class Dataset:
    name: str
    rows: list[dict]
    description: str = ""


@dataclass
class EvalResult:
    prompt_name: str
    dataset_name: str
    row_index: int
    provider: str
    model: str
    rendered_prompt: str
    response: LLMResponse | None = None
    quality_score: float | None = None
    quality_reasoning: str | None = None
    estimated_cost: float = 0.0
    security_findings: list[SecurityFinding] = field(default_factory=list)
    error: str | None = None


def load_prompts(prompts_dir: str) -> list[PromptTemplate]:
    """Load prompt templates from YAML/JSON files in a directory."""
    prompts = []
    path = Path(prompts_dir)
    if not path.exists():
        raise click.ClickException(f"Prompts directory not found: {prompts_dir}")

    for f in sorted(path.iterdir()):
        if f.suffix not in (".yaml", ".yml", ".json"):
            continue
        raw = f.read_text()
        if f.suffix == ".json":
            import json
            data = json.loads(raw)
        else:
            data = yaml.safe_load(raw)

        prompts.append(PromptTemplate(
            name=data.get("name", f.stem),
            template=data["template"],
            variables=data.get("variables", []),
            description=data.get("description", ""),
        ))

    if not prompts:
        raise click.ClickException(f"No prompt files found in {prompts_dir}")
    return prompts


def load_datasets(datasets_dir: str) -> list[Dataset]:
    """Load datasets from YAML/JSON files in a directory."""
    datasets = []
    path = Path(datasets_dir)
    if not path.exists():
        raise click.ClickException(f"Datasets directory not found: {datasets_dir}")

    for f in sorted(path.iterdir()):
        if f.suffix not in (".yaml", ".yml", ".json"):
            continue
        raw = f.read_text()
        if f.suffix == ".json":
            import json
            data = json.loads(raw)
        else:
            data = yaml.safe_load(raw)

        datasets.append(Dataset(
            name=data.get("name", f.stem),
            rows=data.get("rows", []),
            description=data.get("description", ""),
        ))

    if not datasets:
        raise click.ClickException(f"No dataset files found in {datasets_dir}")
    return datasets


async def _run_single(
    semaphore: asyncio.Semaphore,
    provider: BaseProvider,
    provider_name: str,
    model: str,
    prompt_template: PromptTemplate,
    dataset: Dataset,
    row_index: int,
    row: dict,
    timeout: int,
) -> EvalResult:
    """Run a single evaluation."""
    rendered = prompt_template.template.format_map(row)
    result = EvalResult(
        prompt_name=prompt_template.name,
        dataset_name=dataset.name,
        row_index=row_index,
        provider=provider_name,
        model=model,
        rendered_prompt=rendered,
    )

    async with semaphore:
        try:
            response = await asyncio.wait_for(
                provider.complete(rendered),
                timeout=timeout,
            )
            result.response = response
            result.estimated_cost = estimate_cost(response)

            # PII scan on response
            pii_findings = scan_for_pii(response.text, provider_name, model)
            result.security_findings.extend(pii_findings)

        except asyncio.TimeoutError:
            result.error = f"Timeout after {timeout}s"
        except Exception as e:
            result.error = str(e)

    return result


async def run_evaluation(config: Config) -> tuple[list[EvalResult], list[SecurityFinding]]:
    """Run the full evaluation pipeline."""
    prompts = load_prompts(config.evaluation.prompts_dir)
    datasets = load_datasets(config.evaluation.datasets_dir)

    click.echo(f"Loaded {len(prompts)} prompt(s), {len(datasets)} dataset(s)")

    # Build provider instances
    active = config.active_providers()
    providers: dict[str, list[tuple[str, BaseProvider]]] = {}

    for name, pconf in active.items():
        for model in pconf.models:
            kwargs = {"api_key": pconf.api_key, "model": model}
            if pconf.base_url:
                kwargs["base_url"] = pconf.base_url
            try:
                provider = get_provider(name, **kwargs)
                if provider.is_available():
                    providers.setdefault(name, []).append((model, provider))
                else:
                    click.echo(f"  Skipping {name}/{model} (not available)", err=True)
            except Exception as e:
                click.echo(f"  Skipping {name}/{model}: {e}", err=True)

    if not providers:
        raise click.ClickException("No available providers. Check your API keys and installed SDKs.")

    total_models = sum(len(v) for v in providers.values())
    click.echo(f"Using {total_models} model(s) across {len(providers)} provider(s)")

    # Build task list
    semaphore = asyncio.Semaphore(config.evaluation.workers)
    tasks = []

    for prompt_template in prompts:
        for dataset in datasets:
            for row_index, row in enumerate(dataset.rows):
                for provider_name, model_list in providers.items():
                    for model, provider in model_list:
                        tasks.append(_run_single(
                            semaphore, provider, provider_name, model,
                            prompt_template, dataset, row_index, row,
                            config.evaluation.timeout,
                        ))

    click.echo(f"Running {len(tasks)} evaluation(s)...")

    # Execute all tasks
    results = []
    completed = 0
    for coro in asyncio.as_completed(tasks):
        result = await coro
        results.append(result)
        completed += 1
        if completed % 5 == 0 or completed == len(tasks):
            click.echo(f"  Progress: {completed}/{len(tasks)}")

    # Quality scoring
    score_cfg = config.scoring
    judge_provider_name = score_cfg.judge_provider
    if judge_provider_name in providers:
        judge_model, judge = providers[judge_provider_name][0]
        click.echo("Running quality scoring (LLM-as-judge)...")
        for result in results:
            if result.response and not result.error:
                score, reasoning = await score_quality(
                    judge, result.rendered_prompt, result.response.text
                )
                result.quality_score = score
                result.quality_reasoning = reasoning
    else:
        click.echo(f"  Judge provider '{judge_provider_name}' not available, skipping quality scoring", err=True)

    # Security audits
    security_findings: list[SecurityFinding] = []

    if config.security.enabled:
        # Collect PII findings from results
        for r in results:
            security_findings.extend(r.security_findings)

        # Flatten providers for security checks
        flat_providers: dict[str, BaseProvider] = {}
        for pname, model_list in providers.items():
            flat_providers[pname] = model_list[0][1]  # Use first model per provider

        if config.security.injection:
            click.echo("Running injection tests...")
            injection_findings = await run_injection_check(flat_providers)
            security_findings.extend(injection_findings)

        if config.security.jailbreak:
            click.echo("Running jailbreak tests...")
            jailbreak_findings = await run_jailbreak_check(flat_providers)
            security_findings.extend(jailbreak_findings)

    # Summary
    errors = sum(1 for r in results if r.error)
    if errors:
        click.echo(f"  {errors} evaluation(s) had errors")

    return results, security_findings
