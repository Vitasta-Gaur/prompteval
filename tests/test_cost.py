"""Tests for cost estimation."""

from prompteval.scoring.cost import estimate_cost
from prompteval.providers.base import LLMResponse


def _make_response(provider, model, input_tokens=100, output_tokens=50):
    return LLMResponse(
        text="test",
        provider=provider,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=500,
    )


def test_anthropic_sonnet_cost():
    resp = _make_response("anthropic", "claude-sonnet-4-20250514", 1000, 500)
    cost = estimate_cost(resp)
    # input: 1000 * 0.003 / 1000 = 0.003, output: 500 * 0.015 / 1000 = 0.0075
    assert abs(cost - 0.0105) < 1e-6


def test_openai_gpt4o_cost():
    resp = _make_response("openai", "gpt-4o", 1000, 1000)
    cost = estimate_cost(resp)
    # input: 1000 * 0.005 / 1000 = 0.005, output: 1000 * 0.015 / 1000 = 0.015
    assert abs(cost - 0.02) < 1e-6


def test_unknown_model_zero_cost():
    resp = _make_response("unknown", "mystery-model", 1000, 1000)
    cost = estimate_cost(resp)
    assert cost == 0.0


def test_ollama_zero_cost():
    resp = _make_response("ollama", "llama3", 5000, 2000)
    cost = estimate_cost(resp)
    assert cost == 0.0
