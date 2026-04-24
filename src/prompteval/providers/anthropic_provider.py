"""Anthropic Claude provider."""

import logging
import time

from prompteval.providers.base import BaseProvider, LLMResponse

logger = logging.getLogger(__name__)

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


class AnthropicProvider(BaseProvider):
    def __init__(self, api_key: str, model: str, **kwargs):
        self.model = model
        self.api_key = api_key
        if HAS_ANTHROPIC:
            self.client = anthropic.AsyncAnthropic(api_key=api_key)

    def is_available(self) -> bool:
        return HAS_ANTHROPIC and bool(self.api_key)

    async def complete(self, prompt: str, **kwargs) -> LLMResponse:
        start = time.perf_counter()
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 1024),
            messages=[{"role": "user", "content": prompt}],
        )
        latency = (time.perf_counter() - start) * 1000

        return LLMResponse(
            text=response.content[0].text,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            latency_ms=round(latency, 2),
            model=self.model,
            provider="anthropic",
        )


def _register():
    from prompteval.providers import register
    register("anthropic")(AnthropicProvider)

_register()
