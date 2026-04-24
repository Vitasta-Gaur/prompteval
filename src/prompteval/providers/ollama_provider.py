"""Ollama local model provider."""

import logging
import time

from prompteval.providers.base import BaseProvider, LLMResponse

logger = logging.getLogger(__name__)

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


class OllamaProvider(BaseProvider):
    def __init__(self, model: str, base_url: str = "http://localhost:11434", **kwargs):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self._client = None

    def _get_client(self) -> "httpx.AsyncClient":
        """Lazy-init and reuse a single AsyncClient for connection pooling."""
        if self._client is None:
            if not HAS_HTTPX:
                raise RuntimeError(
                    "OllamaProvider requires 'httpx'. Install it with: pip install httpx"
                )
            import httpx as _httpx
            self._client = _httpx.AsyncClient()
        return self._client

    def is_available(self) -> bool:
        if not HAS_HTTPX:
            return False
        try:
            resp = httpx.get(f"{self.base_url}/api/tags", timeout=2)
            return resp.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            return False

    async def complete(self, prompt: str, **kwargs) -> LLMResponse:
        client = self._get_client()
        start = time.perf_counter()
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
