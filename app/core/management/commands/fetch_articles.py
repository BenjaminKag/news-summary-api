from django.core.management.base import BaseCommand
from core.services.ingest import fetch_and_store_articles, NewsApiError
from django.core.management.base import CommandError


class Command(BaseCommand):
    help = "Fetch articles from NewsAPI and upsert them by URL."

    def add_arguments(self, parser):
        parser.add_argument("--q", default="technology")
        parser.add_argument("--page-size", type=int, default=50)

    def handle(self, *args, **opts):
        q = opts["q"]
        page_size = opts["page_size"]
        try:
            created, updated = fetch_and_store_articles(
                keyword=q,
                page_size=page_size
                )
        except NewsApiError as exc:
            raise CommandError("Failed to fetch or store articles.") from exc
        self.stdout.write(self.style.SUCCESS(
            f"Created: {created}, Updated: {updated}"
            ))
