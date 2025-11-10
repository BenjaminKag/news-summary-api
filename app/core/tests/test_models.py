"""
Tests for core models.
"""
from django.test import TestCase
from django.db import IntegrityError
from django.db.models import ProtectedError
from django.utils import timezone

from core.models import Source, Topic, Article, Summary


class ModelTests(TestCase):
    def setUp(self):
        self.bbc = Source.objects.create(
            name="BBC News",
            homepage="https://www.bbc.com/news",
        )
        self.tech = Topic.objects.create(name="Technology")

    def test_slug_is_auto_generated(self):
        """Test that slugs are auto-generated on save."""
        self.assertEqual(self.bbc.slug, "bbc-news")
        self.assertEqual(self.tech.slug, "technology")

    # --- Source / Topic Tests ---

    def test_source_str(self):
        """Test the string representation of Source."""
        self.assertEqual(str(self.bbc), "BBC News")

    def test_topic_str(self):
        """Test the string representation of Topic."""
        self.assertEqual(str(self.tech), "Technology")

    def test_source_name_unique(self):
        """Test that Source names are unique."""
        with self.assertRaises(IntegrityError):
            Source.objects.create(
                name="BBC News",
                slug="bbc-news-2",
                homepage="https://different.com"
            )

    def test_source_slug_unique(self):
        """Test that Source slugs are unique."""
        with self.assertRaises(IntegrityError):
            Source.objects.create(
                name="Different Name",
                slug="bbc-news",
                homepage="https://different.com"
            )

    def test_source_homepage_unique(self):
        """Test that Source homepages are unique."""
        with self.assertRaises(IntegrityError):
            Source.objects.create(
                name="Another Name",
                slug="another-slug",
                homepage="https://www.bbc.com/news"
            )

    def test_topic_name_unique(self):
        """Test that Topic names are unique."""
        with self.assertRaises(IntegrityError):
            Topic.objects.create(name="Technology", slug="another-slug")

    def test_topic_slug_unique(self):
        """Test that Topic slugs are unique."""
        with self.assertRaises(IntegrityError):
            Topic.objects.create(name="Another Name", slug="technology")

    # --- Article Tests ---

    def test_article_create_and_str_truncation(self):
        """Test creating an Article and its string representation."""
        long_title = "X" * 255
        art = Article.objects.create(
            title=long_title,
            url="https://example.com/a1",
            source=self.bbc,
            published_at=timezone.now(),
            author="Jane",
            content="Full text",
        )
        self.assertEqual(len(str(art)), 120)

    def test_article_url_unique(self):
        """Test that Article URLs are unique."""
        Article.objects.create(
            title="A",
            url="https://example.com/u",
            source=self.bbc,
            published_at=timezone.now(),
            content="text",
        )
        with self.assertRaises(IntegrityError):
            Article.objects.create(
                title="B",
                url="https://example.com/u",
                source=self.bbc,
                published_at=timezone.now(),
                content="text",
            )

    def test_article_topics_m2m(self):
        """Test ManyToMany relationship between Article and Topic."""
        art = Article.objects.create(
            title="AI piece",
            url="https://example.com/ai",
            source=self.bbc,
            published_at=timezone.now(),
            content="text",
        )
        art.topics.add(self.tech)
        self.assertEqual(list(art.topics.values_list("slug", flat=True)),
                         ["technology"])

    def test_article_ordering_newest_first(self):
        """Test that Articles are ordered by published_at descending."""
        Article.objects.create(
            title="Old",
            url="https://example.com/old",
            source=self.bbc,
            published_at=timezone.now() - timezone.timedelta(days=1),
            content="old",
        )
        Article.objects.create(
            title="New",
            url="https://example.com/new",
            source=self.bbc,
            published_at=timezone.now(),
            content="new",
        )
        titles = list(Article.objects.values_list("title", flat=True))
        self.assertEqual(titles[0], "New")
        self.assertEqual(titles[1], "Old")

    def test_source_protect_prevents_delete_with_articles(self):
        """Test that deleting a Source with Articles raises ProtectedError."""
        Article.objects.create(
            title="Protected",
            url="https://example.com/protected",
            source=self.bbc,
            published_at=timezone.now(),
            content="text",
        )
        with self.assertRaises(ProtectedError):
            self.bbc.delete()

    # --- Summary ---

    def test_summary_onetoone_enforced(self):
        """Test that only one Summary can be created per Article."""
        art = Article.objects.create(
            title="Sum",
            url="https://example.com/sum",
            source=self.bbc,
            published_at=timezone.now(),
            content="text",
        )
        Summary.objects.create(article=art,
                               text="t1",
                               model_name="baseline")
        with self.assertRaises(IntegrityError):
            Summary.objects.create(article=art,
                                   text="t2",
                                   model_name="baseline")

    def test_summary_str(self):
        art = Article.objects.create(
            title="The Title",
            url="https://example.com/sum",
            source=self.bbc,
            published_at=timezone.now(),
            content="text",
        )
        s = Summary.objects.create(article=art,
                                   text="short text",
                                   model_name="baseline")
        self.assertIn("The Title", str(s))
