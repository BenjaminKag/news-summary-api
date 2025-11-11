"""
Service to ingest articles from an external news API.
"""
import os
import requests
from urllib.parse import urlparse
from django.utils.dateparse import parse_datetime
from core.models import Source, Article

NEWS_API_KEY = os.environ["NEWS_API_KEY"]
NEWS_API_URL = "https://newsapi.org/v2/everything"


def fetch_and_store_articles(keyword: str = "technology", page_size: int = 50):
    """Fetch articles and store/update by URL uniqueness."""
    params = {
        "q": keyword,
        "pageSize": page_size,
        "language": "en",
        "sortBy": "publishedAt",
        "apiKey": NEWS_API_KEY,
    }
    r = requests.get(NEWS_API_URL, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    created, updated = 0, 0

    for item in data.get("articles", []):
        url = item.get("url")
        if not url:
            continue
        parsed = urlparse(url)

        if parsed.scheme and parsed.netloc:
            homepage = f"{parsed.scheme}://{parsed.netloc}"
        else:
            homepage = ""

        src_name = (item.get("source") or {}).get("name") or "Unknown"
        source, _ = Source.objects.get_or_create(
            name=src_name,
            defaults={"homepage": homepage}
            )

        defaults = {
            "title": item.get("title") or "",
            "source": source,
            "published_at": parse_datetime(item.get("publishedAt")) or None,
            "author": item.get("author") or "",
            "content": item.get("content") or (item.get("description") or ""),
        }
        _, was_created = Article.objects.update_or_create(
            url=url,
            defaults=defaults
            )
        created += 1 if was_created else 0
        updated += 0 if was_created else 1
    return created, updated
