"""OpenAI GPT provider."""

import logging
import time

from prompteval.providers.base import BaseProvider, LLMResponse

logger = logging.getLogger(__name__)

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


class OpenAIProvider(BaseProvider):
    def __init__(self, api_key: str, model: str, **kwargs):
        self.model = model
        self.api_key = api_key
        self.client = None
        if HAS_OPENAI and api_key:
            self.client = openai.AsyncOpenAI(api_key=api_key)

    def is_available(self) -> bool:
        return HAS_OPENAI and bool(self.api_key)

    async def complete(self, prompt: str, **kwargs) -> LLMResponse:
        if self.client is None:
            raise RuntimeError(
                "OpenAIProvider is not available. "
                "Install the 'openai' package and provide a valid API key."
            )
        start = time.perf_counter()
        response = await self.client.chat.completions.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 1024),
            messages=[{"role": "user", "content": prompt}],
        )
        latency = (time.perf_counter() - start) * 1000

        usage = response.usage
        return LLMResponse(
            text=response.choices[0].message.content,
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
            latency_ms=round(latency, 2),
            model=self.model,
            provider="openai",
        )


def _register():
    from prompteval.providers import register
    register("openai")(OpenAIProvider)

_register()
