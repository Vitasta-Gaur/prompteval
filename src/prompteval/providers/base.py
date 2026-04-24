"""Abstract base provider and response model."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResponse:
    text: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    model: str
    provider: str


class BaseProvider(ABC):
    @abstractmethod
    async def complete(self, prompt: str, **kwargs) -> LLMResponse:
        """Send a prompt and return a structured response."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider SDK is installed and configured."""
        ...
