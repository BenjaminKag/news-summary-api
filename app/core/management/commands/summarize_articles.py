from django.core.management.base import BaseCommand
from core.models import Article, Summary
from core.services.summarizer import summarize_text
import os

MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


class Command(BaseCommand):
    help = "Create Summaries for articles."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=25)

    def handle(self, *args, **opts):
        qs = (
            Article.objects
            .filter(summary__isnull=True)
            .only("id", "content")[:opts["limit"]]
            )

        count = 0
        for art in qs:
            content = (art.content or "").strip()
            if not content:
                continue
            txt = summarize_text(content)
            Summary.objects.get_or_create(
                article=art,
                defaults={"text": txt, "model_name": MODEL_NAME},
            )
            count += 1
        self.stdout.write(self.style.SUCCESS(
            f"Summarized {count} article(s) using model '{MODEL_NAME}'."
        ))
