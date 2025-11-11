from django.core.management.base import BaseCommand
from core.models import Article
from core.services.tagger import tag_article


class Command(BaseCommand):
    help = "Auto-assign topics to articles based on simple keyword matching."

    def add_arguments(self, parser):
        parser.add_argument(
            "--all",
            action="store_true",
            help="Retag all articles (default: only those without topics)"
            )

    def handle(self, *args, **opts):
        if opts["all"]:
            qs = Article.objects.only("id", "title", "content")
        else:
            qs = (
                Article.objects.
                filter(topics__isnull=True).
                only("id", "title", "content")
                )

        total = 0
        attached = 0
        for a in qs.iterator():
            total += 1
            attached += tag_article(a)

        self.stdout.write(self.style.SUCCESS(
            f"Processed {total} article(s); attached {attached} topic(s)."
        ))
