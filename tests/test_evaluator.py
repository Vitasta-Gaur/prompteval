"""Tests for the evaluation engine."""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock

import click
import pytest

from prompteval.evaluator import (
    EvalResult,
    PromptTemplate,
    Dataset,
    _run_single,
    load_prompts,
    load_datasets,
)
from prompteval.providers.base import BaseProvider, LLMResponse


class MockProvider(BaseProvider):
    """A mock provider that returns canned responses."""

    def __init__(self, response_text="Mock response", fail=False):
        self.response_text = response_text
        self.fail = fail

    def is_available(self) -> bool:
        return True

    async def complete(self, prompt: str, **kwargs) -> LLMResponse:
        if self.fail:
            raise RuntimeError("Mock provider failure")
        return LLMResponse(
            text=self.response_text,
            input_tokens=50,
            output_tokens=25,
            latency_ms=100.0,
            model="mock-model",
            provider="mock",
        )


@pytest.fixture
def prompt_template():
    return PromptTemplate(
        name="test-prompt",
        template="Summarize: {text}",
        variables=["text"],
    )


@pytest.fixture
def dataset():
    return Dataset(
        name="test-dataset",
        rows=[{"text": "Hello world"}, {"text": "Foo bar"}],
    )


def test_run_single_success(prompt_template, dataset):
    provider = MockProvider()
    semaphore = asyncio.Semaphore(4)

    result = asyncio.get_event_loop().run_until_complete(
        _run_single(semaphore, provider, "mock", "mock-model",
                     prompt_template, dataset, 0, dataset.rows[0], timeout=10)
    )

    assert result.response is not None
    assert result.response.text == "Mock response"
    assert result.error is None
    assert result.rendered_prompt == "Summarize: Hello world"


def test_run_single_provider_failure(prompt_template, dataset):
    provider = MockProvider(fail=True)
    semaphore = asyncio.Semaphore(4)

    result = asyncio.get_event_loop().run_until_complete(
        _run_single(semaphore, provider, "mock", "mock-model",
                     prompt_template, dataset, 0, dataset.rows[0], timeout=10)
    )

    assert result.response is None
    assert result.error is not None
    assert "Mock provider failure" in result.error


def test_run_single_template_error(dataset):
    bad_template = PromptTemplate(
        name="bad-prompt",
        template="Missing var: {nonexistent}",
        variables=["nonexistent"],
    )
    provider = MockProvider()
    semaphore = asyncio.Semaphore(4)

    result = asyncio.get_event_loop().run_until_complete(
        _run_single(semaphore, provider, "mock", "mock-model",
                     bad_template, dataset, 0, dataset.rows[0], timeout=10)
    )

    assert result.error is not None
    assert "Template render failed" in result.error
    assert "bad-prompt" in result.error


def test_run_single_pii_scan(dataset):
    provider = MockProvider(response_text="Contact: user@example.com")
    semaphore = asyncio.Semaphore(4)

    result = asyncio.get_event_loop().run_until_complete(
        _run_single(semaphore, asyncio.Semaphore(4) and provider, "mock", "mock-model",
                     PromptTemplate(name="t", template="{text}", variables=["text"]),
                     dataset, 0, dataset.rows[0], timeout=10)
    )

    assert len(result.security_findings) > 0
    assert any("email" in f.description.lower() for f in result.security_findings)


def test_load_prompts():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "prompt1.yaml").write_text(
            'name: "test"\ntemplate: "Hello {name}"\nvariables: ["name"]'
        )
        prompts = load_prompts(tmpdir)
        assert len(prompts) == 1
        assert prompts[0].name == "test"
        assert prompts[0].template == "Hello {name}"


def test_load_prompts_empty_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(click.ClickException, match="No prompt files"):
            load_prompts(tmpdir)


def test_load_datasets():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "data.yaml").write_text(
            'name: "test"\nrows:\n  - text: "hello"\n  - text: "world"'
        )
        datasets = load_datasets(tmpdir)
        assert len(datasets) == 1
        assert len(datasets[0].rows) == 2


def test_load_datasets_empty_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(click.ClickException, match="No dataset files"):
            load_datasets(tmpdir)
