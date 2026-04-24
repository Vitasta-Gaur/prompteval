"""Token cost estimation."""

from prompteval.providers.base import LLMResponse

# Prices per 1K tokens (input, output) — last updated April 2026
# Source: provider pricing pages. Review and update periodically.
PRICING: dict[tuple[str, str], tuple[float, float]] = {
    # Anthropic
    ("anthropic", "claude-sonnet-4-20250514"): (0.003, 0.015),
    ("anthropic", "claude-haiku-4-5-20251001"): (0.0008, 0.004),
    ("anthropic", "claude-opus-4-20250514"): (0.015, 0.075),
    # OpenAI
    ("openai", "gpt-4o"): (0.005, 0.015),
    ("openai", "gpt-4o-mini"): (0.00015, 0.0006),
    ("openai", "gpt-4-turbo"): (0.01, 0.03),
    # Gemini
    ("gemini", "gemini-1.5-pro"): (0.00125, 0.005),
    ("gemini", "gemini-1.5-flash"): (0.000075, 0.0003),
    # Ollama — free (local)
}


def estimate_cost(response: LLMResponse) -> float:
    """Estimate cost in USD for a single LLM response."""
    rates = PRICING.get((response.provider, response.model), (0.0, 0.0))
    return (response.input_tokens * rates[0] + response.output_tokens * rates[1]) / 1000
