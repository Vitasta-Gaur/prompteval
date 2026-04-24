# Contributing to PromptEval

Thanks for your interest in contributing to PromptEval! This guide will help you get started.

## Getting Started

### Prerequisites

- Python 3.10+
- Git

### Setup

1. Fork and clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/prompteval.git
cd prompteval
```

2. Create a virtual environment and install in development mode:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[all,dev]"
```

3. Verify the installation:

```bash
prompteval --version
```

## Project Structure

```
prompteval/
├── src/prompteval/
│   ├── cli.py                 # CLI entry point (Click)
│   ├── config.py              # Config loading, validation, scaffolding
│   ├── evaluator.py           # Core evaluation engine
│   ├── providers/             # LLM provider implementations
│   │   ├── base.py            # BaseProvider ABC + LLMResponse dataclass
│   │   ├── anthropic_provider.py
│   │   ├── openai_provider.py
│   │   ├── gemini_provider.py
│   │   └── ollama_provider.py
│   ├── scoring/
│   │   ├── cost.py            # Token cost estimation
│   │   └── quality.py         # LLM-as-judge scoring
│   ├── security/
│   │   ├── pii.py             # PII regex detection + SecurityFinding model
│   │   ├── injection.py       # Prompt injection tests
│   │   └── jailbreak.py       # Jailbreak resistance tests
│   ├── report/
│   │   ├── generator.py       # Report data aggregation + rendering
│   │   └── template.html      # Jinja2 HTML template
│   └── templates/             # Scaffolding templates for `prompteval init`
├── tests/
├── pyproject.toml
├── README.md
└── CONTRIBUTING.md
```

## How to Contribute

### Reporting Bugs

Open an issue with:
- What you expected to happen
- What actually happened
- Steps to reproduce
- Python version and OS

### Suggesting Features

Open an issue describing:
- The problem you're trying to solve
- Your proposed solution
- Any alternatives you've considered

### Submitting Code

1. Create a branch from `main`:

```bash
git checkout -b feature/your-feature-name
```

2. Make your changes following the guidelines below.

3. Run tests:

```bash
pytest
```

4. Commit with a clear message:

```bash
git commit -m "Add support for X provider"
```

5. Push and open a pull request.

## Contribution Areas

Here are some ways you can help:

### Adding a New Provider

1. Create `src/prompteval/providers/your_provider.py`
2. Subclass `BaseProvider` from `base.py`
3. Implement `complete()` (async) and `is_available()`
4. Register with `@register("your-provider")` or use the `_register()` pattern
5. Import the module in `providers/__init__.py`
6. Add pricing to `scoring/cost.py` if applicable
7. Add the SDK to `pyproject.toml` as an optional dependency

### Adding a Security Check

1. Create `src/prompteval/security/your_check.py`
2. Implement an async function: `async def run_your_check(providers, ...) -> list[SecurityFinding]`
3. Use the `SecurityFinding` dataclass from `security/pii.py`
4. Register in `security/__init__.py` SECURITY_CHECKS dict
5. Add a config flag in `SecurityConfig` (in `config.py`)
6. Wire it into the evaluation pipeline in `evaluator.py`

### Improving the Report

The report template is at `src/prompteval/report/template.html`. It uses:
- **Jinja2** for templating
- **Chart.js** (loaded via CDN) for charts
- Plain CSS (no framework)

Data is prepared in `report/generator.py` and passed as template context. To add a new chart or section:
1. Add a `_build_*` function in `generator.py`
2. Pass the data in the `context` dict
3. Add the HTML/JS in `template.html`

### Updating Pricing

Model pricing in `scoring/cost.py` goes stale. If you notice outdated prices, update the `PRICING` dict with current rates.

## Code Guidelines

- **Keep it simple.** PromptEval's value is in being lightweight. Avoid adding heavy dependencies.
- **Use dataclasses** for models, not pydantic (core code only — providers may use pydantic transitively).
- **Async by default.** Provider methods are async. Use `asyncio.to_thread()` for sync SDKs.
- **Handle errors gracefully.** A single failed API call should never crash the entire run. Catch, log, and continue.
- **No print statements.** Use `click.echo()` for user output and `logging` for debug info.
- **Type hints.** Use them for function signatures. Python 3.10+ syntax (`X | None` instead of `Optional[X]`).

## Testing

### Unit Tests

```bash
pytest tests/
```

- Mock all API calls — never call real APIs in unit tests
- Use the fixtures in `tests/fixtures/` for sample configs and data

### Integration Tests

For testing with real APIs (not run in CI):

```bash
PROMPTEVAL_INTEGRATION=1 pytest tests/integration/
```

Requires API keys set as environment variables.

## Code of Conduct

Be respectful and constructive. We're all here to build something useful.

## Questions?

Open an issue or start a discussion. We're happy to help you get started.
