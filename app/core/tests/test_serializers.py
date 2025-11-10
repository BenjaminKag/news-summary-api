"""
Tests for core serializers.
"""
from django.test import TestCase
from django.utils import timezone
from core.models import Source, Topic, Article, Summary
from core.serializers import (
    SourceSerializer,
    TopicSerializer,
    ArticleSerializer,
    SummarySerializer,
)


class SerializerTests(TestCase):
    def setUp(self):
        self.source = Source.objects.create(
            name="Test Source",
            homepage="https://www.testsource.com",
        )
        self.topic = Topic.objects.create(name="Test Topic")
        self.article = Article.objects.create(
            title="Test Article",
            url="https://www.testsource.com/test-article",
            source=self.source,
            published_at=timezone.now(),
            author="Test Author",
            content="This is a test article content.",
        )
        self.article.topics.add(self.topic)
        self.summary = Summary.objects.create(
            article=self.article,
            text="This is a test summary.",
        )

    def test_source_serializer(self):
        """SourceSerializer should include id, name, slug, homepage."""
        serializer = SourceSerializer(self.source)
        data = serializer.data

        self.assertEqual(
            set(data.keys()), {"id", "name", "slug", "homepage"}
        )
        self.assertIsInstance(data["id"], int)
        self.assertEqual(data['name'], "Test Source")
        self.assertEqual(data['slug'], "test-source")
        self.assertEqual(data['homepage'], "https://www.testsource.com")

    def test_topic_serializer(self):
        """TopicSerializer should include id, name, slug."""
        serializer = TopicSerializer(self.topic)
        data = serializer.data

        self.assertEqual(
            set(data.keys()), {"id", "name", "slug"}
        )
        self.assertIsInstance(data["id"], int)
        self.assertEqual(data['name'], "Test Topic")
        self.assertEqual(data['slug'], "test-topic")

    def test_summary_serializer(self):
        """SummarySerializer should include text and model_name."""
        serializer = SummarySerializer(self.summary)
        data = serializer.data

        self.assertEqual(
            set(data.keys()), {"text", "model_name"}
        )
        self.assertNotIn("id", data)
        self.assertNotIn("article", data)
        self.assertEqual(data['text'], "This is a test summary.")
        self.assertEqual(data['model_name'], "baseline")

    def test_summary_serializer_is_read_only(self):
        """SummarySerializer should be read-only."""
        serializer = SummarySerializer(data={
            "text": "new text",
            "model_name": "v2"
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn("text", serializer.errors)
        self.assertIn("model_name", serializer.errors)

    def test_article_serializer(self):
        """ArticleSerializer should include all fields."""
        serializer = ArticleSerializer(self.article)
        data = serializer.data

        expected_fields = {
            "id", "title", "url", "source", "published_at",
            "author", "content", "topics", "summary"
        }

        self.assertEqual(set(data.keys()), expected_fields)
        self.assertIsInstance(data["id"], int)
        self.assertEqual(data['title'], "Test Article")
        self.assertEqual(data['url'],
                         "https://www.testsource.com/test-article")
        self.assertIsInstance(data['published_at'], str)
        self.assertEqual(data['content'], "This is a test article content.")
        self.assertEqual(data['author'], "Test Author")

        self.assertIsInstance(data["source"], dict)
        self.assertEqual(set(data["source"].keys()), {"id",
                                                      "name",
                                                      "slug",
                                                      "homepage"})
        self.assertEqual(data["source"]["slug"], "test-source")

        self.assertIsInstance(data["topics"], list)
        self.assertEqual(len(data["topics"]), 1)
        self.assertEqual(set(data["topics"][0].keys()), {"id", "name", "slug"})
        self.assertEqual(data["topics"][0]["slug"], "test-topic")

        self.assertIsInstance(data['summary'], dict)
        self.assertEqual(set(data["summary"].keys()), {"text", "model_name"})
        self.assertEqual(data['summary']['text'], "This is a test summary.")

    def test_article_serializer_create_valid_data(self):
        """Serializer should create an Article when input is valid."""
        payload = {
            "title": "New Article",
            "url": "https://example.com/new",
            "source_id": self.source.id,
            "published_at": timezone.now(),
            "author": "Author",
            "content": "Some text",
        }
        serializer = ArticleSerializer(data=payload)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        article = serializer.save()
        self.assertEqual(article.title, payload["title"])

    def test_article_serializer_missing_fields_invalid(self):
        """Serializer should be invalid when required fields missing."""
        serializer = ArticleSerializer(data={"title": "Incomplete"})
        self.assertFalse(serializer.is_valid())
        self.assertIn("url", serializer.errors)
