"""LLM-as-judge quality scoring."""

import json
import logging

from prompteval.providers.base import BaseProvider

logger = logging.getLogger(__name__)

JUDGE_PROMPT = """Rate the following AI response on a scale of 1-10 for quality, relevance, and completeness.
Respond with ONLY a JSON object: {{"score": <int>, "reasoning": "<brief explanation>"}}

Original prompt: {prompt}

AI response: {response}"""


async def score_quality(
    judge: BaseProvider,
    prompt: str,
    response_text: str,
) -> tuple[float | None, str | None]:
    """Score a response using LLM-as-judge. Returns (score, reasoning) or (None, None) on failure."""
    try:
        judge_input = JUDGE_PROMPT.format(prompt=prompt, response=response_text)
        result = await judge.complete(judge_input)
        data = json.loads(result.text)
        return float(data["score"]), data.get("reasoning")
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        logger.warning(f"Failed to parse judge response: {e}")
        logger.debug(f"Raw judge response: {result.text if 'result' in dir() else 'N/A'}")
        return None, None
    except Exception as e:
        logger.warning(f"Judge scoring failed: {e}")
        return None, None
