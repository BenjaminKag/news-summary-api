from core.models import Topic, Article

TOPIC_KEYWORDS = {
    "AI": ["ai", "artificial intelligence", "machine learning", "ml", "llm"],
    "Python": ["python"],
    "Django": ["django", "rest framework", "drf"],
    "Docker": ["docker", "container", "kubernetes", "k8s"],
    "AWS": ["aws", "amazon web services", "ec2", "s3", "lambda"],
    "Security": ["security", "vulnerability", "breach", "cyber", "ransomware"],
    "Databases": ["postgres", "mysql", "sqlite", "database", "sql", "nosql"],
    "Web": ["frontend", "backend", "api", "microservice", "http", "rest"],
    "Cloud": ["cloud", "gcp", "azure", "cloudflare"],
}


def _guess_topics(text: str) -> list[str]:
    """Simple keyword-based topic guessing from text."""
    t = (text or "").lower()
    matched = []
    for canonical, keywords in TOPIC_KEYWORDS.items():
        if any(kw in t for kw in keywords):
            matched.append(canonical)
    return matched


def tag_article(article: Article, max_topics: int = 5) -> int:
    """ Attach Topics to articles."""
    blob = f"{article.title}\n{article.content or ''}"
    names = _guess_topics(blob)[:max_topics]
    if not names:
        return 0
    topics = []
    for name in names:
        topic, _ = Topic.objects.get_or_create(name=name)
        topics.append(topic)
    if topics:
        article.topics.add(*topics)
    return len(topics)
