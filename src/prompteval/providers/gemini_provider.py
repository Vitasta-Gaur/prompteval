"""Google Gemini provider."""

import logging
import time

from prompteval.providers.base import BaseProvider, LLMResponse

logger = logging.getLogger(__name__)

try:
    from google import genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False


class GeminiProvider(BaseProvider):
    def __init__(self, api_key: str, model: str, **kwargs):
        self.model = model
        self.api_key = api_key
        self.client = None
        if HAS_GEMINI and api_key:
            self.client = genai.Client(api_key=api_key)

    def is_available(self) -> bool:
        return HAS_GEMINI and bool(self.api_key)

    async def complete(self, prompt: str, **kwargs) -> LLMResponse:
        if self.client is None:
            raise RuntimeError(
                "GeminiProvider is not available. "
                "Install the 'google-genai' package and provide a valid API key."
            )
        start = time.perf_counter()
        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
        )
        latency = (time.perf_counter() - start) * 1000

        metadata = response.usage_metadata
        return LLMResponse(
            text=response.text,
            input_tokens=getattr(metadata, "prompt_token_count", 0),
            output_tokens=getattr(metadata, "candidates_token_count", 0),
            latency_ms=round(latency, 2),
            model=self.model,
            provider="gemini",
        )


def _register():
    from prompteval.providers import register
    register("gemini")(GeminiProvider)

_register()
