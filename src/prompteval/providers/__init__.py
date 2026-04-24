"""LLM provider registry."""

from prompteval.providers.base import BaseProvider, LLMResponse

PROVIDER_REGISTRY: dict[str, type[BaseProvider]] = {}


def register(name: str):
    """Decorator to register a provider class."""
    def decorator(cls):
        PROVIDER_REGISTRY[name] = cls
        return cls
    return decorator


def get_provider(name: str, **kwargs) -> BaseProvider:
    """Instantiate a registered provider by name."""
    if name not in PROVIDER_REGISTRY:
        raise ValueError(f"Unknown provider: {name}. Available: {list(PROVIDER_REGISTRY.keys())}")
    return PROVIDER_REGISTRY[name](**kwargs)


# Import providers to trigger registration
from prompteval.providers import anthropic_provider, openai_provider, gemini_provider, ollama_provider  # noqa: E402, F401

__all__ = ["BaseProvider", "LLMResponse", "PROVIDER_REGISTRY", "register", "get_provider"]
