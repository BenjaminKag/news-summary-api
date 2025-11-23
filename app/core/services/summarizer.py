"""
Service to summarize article text using OpenAI API.
"""
import os
import logging
from openai import OpenAI, APIError, RateLimitError

MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
API_KEY = os.getenv("OPENAI_API_KEY")

logger = logging.getLogger(__name__)

client = OpenAI(api_key=API_KEY) if API_KEY else None


def _fallback_summary(text: str) -> str:
    """Simple offline fallback: first few sentences."""
    sentences = [s.strip() for s in (text or "").split(".") if s.strip()]
    return ". ".join(sentences[:5]) + ("." if sentences else "")


def summarize_text(text: str) -> str:
    """
    Return a 4–6 sentence summary of the given text.

    Falls back to a simple extraction summary if OpenAI
    is unavailable or if the API call fails.
    """
    if client is None:
        return _fallback_summary(text)

    prompt = (
        "Summarize the following news article in 4–6 sentences. "
        "Keep it factual and neutral, no bullet points:\n\n" + text
    )
    try:
        # client = OpenAI(api_key=...)
        # initializes a lightweight HTTP client
        # client.responses.create(...)
        # sends an HTTP request to OpenAI’s API
        resp = client.responses.create(model=MODEL_NAME, input=prompt)
        return (resp.output_text or "").strip() or _fallback_summary(text)
    except (RateLimitError, APIError, Exception) as exc:
        logger.warning("Summarization failed; using fallback summary.",
                       exc_info=exc)
        return _fallback_summary(text)
