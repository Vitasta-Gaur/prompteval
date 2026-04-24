# PromptEval

A lightweight, self-hosted prompt evaluation and security auditing tool for LLMs. Test your prompts across multiple providers, measure quality, track costs, and catch security vulnerabilities — all from a single CLI command.

## Why PromptEval?

You write prompts. But how do you know they're good? PromptEval lets you:

- **Compare prompts** across Anthropic, OpenAI, Gemini, and local models (Ollama)
- **Score quality** using LLM-as-judge evaluation
- **Track token usage and costs** per provider and model
- **Detect security issues** — prompt injection, PII leakage, and jailbreak vulnerabilities
- **Generate a single HTML report** you can share with your team


## Quick Start

### Install

```bash
pip install prompteval

# Install with specific providers
pip install "prompteval[anthropic]"
pip install "prompteval[openai]"
pip install "prompteval[google]"
pip install "prompteval[all]"   # All providers
```

### Initialize

```bash
mkdir my-eval && cd my-eval
prompteval init
```

This creates:

```
my-eval/
├── config.yaml              # API keys and settings
├── prompts/
│   └── summarize.yaml       # Sample prompt template
└── datasets/
    └── articles.yaml        # Sample test data
```

### Configure

Edit `config.yaml` with your API keys (or use environment variables):

```yaml
providers:
  anthropic:
    api_key: "${ANTHROPIC_API_KEY}"
    models:
      - claude-sonnet-4-20250514
  openai:
    api_key: "${OPENAI_API_KEY}"
    models:
      - gpt-4o
  ollama:
    base_url: "http://localhost:11434"
    models:
      - llama3
```

### Add Prompts

Create YAML or JSON files in `prompts/`:

```yaml
name: "summarize"
description: "Summarize a given text concisely"
template: |
  Summarize the following text in 2-3 sentences:

  {text}
variables:
  - text
```

### Add Datasets

Create YAML or JSON files in `datasets/`:

```yaml
name: "articles"
rows:
  - text: "Artificial intelligence has transformed numerous industries..."
  - text: "The global renewable energy market has experienced..."
```

### Run

```bash
prompteval run
```

Options:

```bash
prompteval run --config config.yaml     # Custom config path
prompteval run --output results.html    # Custom output path
prompteval run --no-security            # Skip security audits
prompteval run --workers 8              # Parallel workers
prompteval run -v                       # Verbose output
prompteval run -vv                      # Debug output
```

## Sample Report

![Sample Report Screenshot](examples/sample_report_screenshot.png)

Check out a [sample report](examples/sample_report.html) to see what PromptEval generates. Download and open it in your browser to explore the interactive charts and tables.

## What the Report Shows

The generated HTML report includes:

### Summary Dashboard
Total runs, success/error counts, average quality score, average latency, total cost, and security issue count.

### Performance Charts
- **Token usage** — input vs output tokens per provider/model (stacked bar)
- **Cost breakdown** — estimated cost per provider/model (doughnut)
- **Latency comparison** — average response time per provider/model (bar)

### Quality Comparison Table
Average quality score, latency, and cost grouped by prompt × provider × model. Scores are color-coded: green (7+), yellow (5-7), red (<5).

### Security Findings
Color-coded by severity (critical, high, medium, low):

- **Prompt Injection** — Tests 12 adversarial prompts to see if models can be tricked into ignoring instructions
- **PII Leakage** — Scans responses for SSNs, emails, credit cards, phone numbers, IP addresses
- **Jailbreak Testing** — Tests DAN-style attacks, roleplay escapes, encoding tricks, and system prompt extraction

### Detailed Results
Expandable table with every individual evaluation: prompt, dataset row, response, tokens, latency, cost, quality score, and errors.

## Configuration Reference

### Providers

```yaml
providers:
  anthropic:
    api_key: "${ANTHROPIC_API_KEY}"     # API key (supports env vars)
    models:
      - claude-sonnet-4-20250514
      - claude-haiku-4-5-20251001
  openai:
    api_key: "${OPENAI_API_KEY}"
    models:
      - gpt-4o
      - gpt-4o-mini
  gemini:
    api_key: "${GEMINI_API_KEY}"
    models:
      - gemini-1.5-pro
  ollama:
    base_url: "http://localhost:11434"   # Custom Ollama URL
    models:
      - llama3
      - mistral
```

### Evaluation Settings

```yaml
evaluation:
  workers: 4          # Parallel API calls
  timeout: 60         # Timeout per call (seconds)
  prompts_dir: "prompts/"
  datasets_dir: "datasets/"
```

### Security Settings

```yaml
security:
  injection: true       # Run prompt injection tests
  pii_detection: true   # Scan for PII in responses
  jailbreak: true       # Run jailbreak resistance tests
```

### Scoring Settings

```yaml
scoring:
  judge_provider: "anthropic"
  judge_model: "claude-sonnet-4-20250514"
```

## Adding Custom Providers

Subclass `BaseProvider` and register it:

```python
from prompteval.providers.base import BaseProvider, LLMResponse
from prompteval.providers import register

@register("my-provider")
class MyProvider(BaseProvider):
    def __init__(self, api_key: str, model: str, **kwargs):
        self.api_key = api_key
        self.model = model

    def is_available(self) -> bool:
        return bool(self.api_key)

    async def complete(self, prompt: str, **kwargs) -> LLMResponse:
        # Call your API here
        return LLMResponse(
            text="response",
            input_tokens=100,
            output_tokens=50,
            latency_ms=500.0,
            model=self.model,
            provider="my-provider",
        )
```

## Requirements

- Python 3.10+
- At least one LLM provider API key (or Ollama running locally)

## License

MIT
