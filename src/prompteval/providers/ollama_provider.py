"""Ollama local model provider."""

import logging
import time

import httpx

from prompteval.providers.base import BaseProvider, LLMResponse

logger = logging.getLogger(__name__)


class OllamaProvider(BaseProvider):
    def __init__(self, model: str, base_url: str = "http://localhost:11434", **kwargs):
        self.model = model
        self.base_url = base_url.rstrip("/")

    def is_available(self) -> bool:
        try:
            resp = httpx.get(f"{self.base_url}/api/tags", timeout=2)
            return resp.status_code == 200
        except httpx.ConnectError:
            return False

    async def complete(self, prompt: str, **kwargs) -> LLMResponse:
        start = time.perf_counter()
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=kwargs.get("timeout", 120),
            )
            resp.raise_for_status()
            data = resp.json()
        latency = (time.perf_counter() - start) * 1000

        return LLMResponse(
            text=data.get("response", ""),
            input_tokens=data.get("prompt_eval_count", 0),
            output_tokens=data.get("eval_count", 0),
            latency_ms=round(latency, 2),
            model=self.model,
            provider="ollama",
        )


def _register():
    from prompteval.providers import register
    register("ollama")(OllamaProvider)

_register()
