"""
Core models for the news summary API.
"""
from django.db import models

from django.utils.text import slugify


class TimeStamped(models.Model):
    """Abstract base class model that provides a 'created_at' field."""
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class Source(TimeStamped):
    """Source Object."""
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    homepage = models.URLField(max_length=1000, unique=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Topic(TimeStamped):
    """Topic Object."""
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Article(TimeStamped):
    """Article Object."""
    title = models.CharField(max_length=255)
    url = models.URLField(max_length=1000, unique=True)
    source = models.ForeignKey(Source, on_delete=models.PROTECT,
                               related_name='articles')
    published_at = models.DateTimeField(db_index=True)
    author = models.CharField(max_length=255, blank=True)
    content = models.TextField(blank=False)
    topics = models.ManyToManyField(Topic, blank=True, related_name='articles')

    class Meta:
        indexes = [models.Index(fields=['published_at'])]
        ordering = ['-published_at']

    def __str__(self):
        return self.title[:120]


class Summary(TimeStamped):
    """Summary Object."""
    article = models.OneToOneField(Article, on_delete=models.CASCADE,
                                   related_name='summary')
    text = models.TextField()
    model_name = models.CharField(max_length=255, default='baseline')

    def __str__(self):
        return f"Summary of {self.article.title[:120]}"
