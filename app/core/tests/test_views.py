"""
Tests for ViewSets.
"""
from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase

from datetime import timedelta

from core.models import Source, Topic, Article, Summary

ARTICLES_URL = reverse("article-list")


def article_detail_url(pk):
    return reverse("article-detail", args=[pk])


def article_summary_url(pk):
    return reverse("article-summary", args=[pk])


class ArticleViewSetTests(APITestCase):
    def setUp(self):
        self.source = Source.objects.create(
            name="Test Source",
            homepage="https://testsource.com"
        )
        self.topic_one = Topic.objects.create(name="First Topic")
        self.topic_two = Topic.objects.create(name="Second Topic")

        now = timezone.now()

        self.article_old = Article.objects.create(
            title="Old Article",
            url="https://testsource.com/old",
            source=self.source,
            published_at=now - timedelta(days=2),
            author="Test Author",
            content="This is the content of the old article.",
        )

        self.article_new = Article.objects.create(
            title="New Article",
            url="https://testsource.com/new",
            source=self.source,
            published_at=now,
            author="Another Author",
            content="This is the content of the new article.",
        )
        self.article_new.topics.add(self.topic_one)
        Summary.objects.create(
            article=self.article_new,
            text="This is a summary of the new article."
        )

    def test_list_articles(self):
        """Tests listing all articles in correct order."""
        res = self.client.get(ARTICLES_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("results", res.data)

        titles = [row["title"] for row in res.data["results"]]

        self.assertEqual(len(titles), 2)
        self.assertEqual(titles[0], "New Article")
        self.assertEqual(titles[1], "Old Article")

    def test_retrieve_article(self):
        """Tests retrieving a specific article by ID."""
        url = article_detail_url(self.article_old.id)
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["id"], self.article_old.id)
        self.assertEqual(res.data["title"], "Old Article")

    def test_article_sumamry_exists(self):
        """Tests retrieving summary for an article that has one."""
        url = article_summary_url(self.article_new.id)
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(set(res.data.keys()), {"text", "model_name"})
        self.assertIn("text", res.data)
        self.assertEqual(res.data["text"],
                         "This is a summary of the new article.")

    def test_article_summary_not_exists(self):
        """Tests retrieving summary for an article that does not have one."""
        url = article_summary_url(self.article_old.id)
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_ordering_param_ascending(self):
        """Tests ordering articles by published_at ascending."""
        res = self.client.get(ARTICLES_URL, {"ordering": "published_at"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        titles = [row["title"] for row in res.data["results"]]
        self.assertEqual(titles, ["Old Article", "New Article"])

    def test_pagination_page_2(self):
        """Tests pagination by requesting the second page."""
        for i in range(25):
            Article.objects.create(
                title=f"Extra {i}",
                url=f"https://testsource.com/extra-{i}",
                source=self.source,
                published_at=timezone.now() - timedelta(minutes=i),
                author="Extra Author",
                content="Extra content.",
            )

        res = self.client.get(ARTICLES_URL, {"page": 2})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("results", res.data)
        self.assertEqual(len(res.data["results"]), 7)

    def test_post_is_read_only(self):
        """Tests that POST requests are not allowed on articles."""
        payload = {
            "title": "Should Fail",
            "url": "https://testsource.com/should-fail",
            "source": self.source.id,
            "published_at": timezone.now().isoformat(),
            "author": "Fail",
            "content": "Fail",
            "topics": [self.topic_one.id],
        }
        res = self.client.post(ARTICLES_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_filter_by_topic_id(self):
        """Tests filtering articles by topic ID."""
        res = self.client.get(ARTICLES_URL, {"topic_ids": self.topic_one.id})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        titles = [row["title"] for row in res.data["results"]]
        self.assertEqual(titles, ["New Article"])

        res_empty = self.client.get(
            ARTICLES_URL,
            {"topic_ids": self.topic_two.id}
            )
        self.assertEqual(res_empty.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_empty.data["results"]), 0)

    def test_filter_by_topic_slug(self):
        """Tests filtering articles by topic slug."""
        res = self.client.get(
            ARTICLES_URL,
            {"topic_slugs": self.topic_one.slug}
            )
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        titles = [row["title"] for row in res.data["results"]]
        self.assertEqual(titles, ["New Article"])

        res_empty = self.client.get(
            ARTICLES_URL,
            {"topic_slugs": self.topic_two.slug}
            )
        self.assertEqual(res_empty.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_empty.data["results"]), 0)

    def test_filter_by_multiple_topic_ids(self):
        """Tests filtering by multiple topic IDs."""
        third = Article.objects.create(
            title="Third Article",
            url="https://testsource.com/third",
            source=self.source,
            published_at=timezone.now(),
            author="Third",
            content="Third content.",
        )
        third.topics.set([self.topic_two])

        res = self.client.get(
            ARTICLES_URL,
            {"topic_ids": f"{self.topic_one.id},{self.topic_two.id}"}
            )
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        titles = [row["title"] for row in res.data["results"]]
        self.assertCountEqual(titles, ["New Article", "Third Article"])

    def test_filter_by_multiple_topic_slugs(self):
        """Tests filtering by multiple topic slugs."""
        third = Article.objects.create(
            title="Third Article",
            url="https://testsource.com/third",
            source=self.source,
            published_at=timezone.now(),
            author="Third",
            content="Third content.",
        )
        third.topics.set([self.topic_two])

        slugs = f"{self.topic_one.slug.upper()},{self.topic_two.slug}"
        res = self.client.get(ARTICLES_URL, {"topic_slugs": slugs})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        titles = [row["title"] for row in res.data["results"]]
        self.assertCountEqual(titles, ["New Article", "Third Article"])
