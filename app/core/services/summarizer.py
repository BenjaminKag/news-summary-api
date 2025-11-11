"""
Service to summarize article text using OpenAI API.
"""
import os
from openai import OpenAI, APIError, RateLimitError

MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
API_KEY = os.getenv("OPENAI_API_KEY")


def _fallback_summary(text: str) -> str:
    """Simple offline fallback: first few sentences."""
    sentences = [s.strip() for s in (text or "").split(".") if s.strip()]
    return ". ".join(sentences[:5]) + ("." if sentences else "")


def summarize_text(text: str) -> str:
    """Return a short summary for article content."""
    if not API_KEY:
        return _fallback_summary(text)

    client = OpenAI(api_key=API_KEY)
    prompt = (
        "Summarize the following news article in 4–6 sentences. "
        "Keep it factual and neutral, no bullet points:\n\n" + text
    )
    try:
        resp = client.responses.create(model=MODEL_NAME, input=prompt)
        return (resp.output_text or "").strip() or _fallback_summary(text)
    except (RateLimitError, APIError, Exception):
        return _fallback_summary(text)
