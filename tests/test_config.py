"""Tests for configuration loading."""

import os
import tempfile
from pathlib import Path

from prompteval.config import load_config, scaffold_project, _resolve_env_vars


def test_resolve_env_vars():
    os.environ["TEST_KEY_PROMPTEVAL"] = "secret123"
    result = _resolve_env_vars("key=${TEST_KEY_PROMPTEVAL}")
    assert result == "key=secret123"
    del os.environ["TEST_KEY_PROMPTEVAL"]


def test_resolve_env_vars_missing():
    result = _resolve_env_vars("key=${NONEXISTENT_VAR_XYZ}")
    assert result == "key="


def test_resolve_env_vars_nested():
    os.environ["TEST_NESTED"] = "val"
    result = _resolve_env_vars({"a": "${TEST_NESTED}", "b": ["${TEST_NESTED}"]})
    assert result == {"a": "val", "b": ["val"]}
    del os.environ["TEST_NESTED"]


def test_load_config_from_yaml():
    config_content = """
providers:
  anthropic:
    api_key: "test-key"
    models: ["claude-sonnet-4-20250514"]
  ollama:
    models: ["llama3"]
evaluation:
  workers: 2
  timeout: 30
security:
  injection: true
  pii_detection: true
  jailbreak: false
scoring:
  judge_provider: anthropic
  judge_model: claude-sonnet-4-20250514
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(config_content)
        f.flush()
        config = load_config(f.name)

    assert config.providers["anthropic"].api_key == "test-key"
    assert config.providers["ollama"].models == ["llama3"]
    assert config.evaluation.workers == 2
    assert config.security.jailbreak is False
    assert config.scoring.judge_model == "claude-sonnet-4-20250514"
    os.unlink(f.name)


def test_scaffold_project():
    with tempfile.TemporaryDirectory() as tmpdir:
        scaffold_project(tmpdir)
        assert (Path(tmpdir) / "config.yaml").exists()
        assert (Path(tmpdir) / "prompts" / "summarize.yaml").exists()
        assert (Path(tmpdir) / "datasets" / "articles.yaml").exists()
