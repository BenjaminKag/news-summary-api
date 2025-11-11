"""
Filters for the Article model.
"""

import django_filters as df
from .models import Article


class ArticleFilter(df.FilterSet):
    topic_ids = df.CharFilter(method="filter_topics_by_ids")
    topic_slugs = df.CharFilter(method="filter_topics_by_slugs")

    class Meta:
        model = Article
        fields = ["topic_ids", "topic_slugs"]

    def filter_topics_by_ids(self, queryset, name, value):
        try:
            ids = [int(v) for v in value.split(",") if v.strip()]
        except ValueError:
            return queryset.none()
        if not ids:
            return queryset
        return queryset.filter(topics__id__in=ids).distinct()

    def filter_topics_by_slugs(self, queryset, name, value):
        slugs = [v.strip().lower() for v in value.split(",") if v.strip()]
        if not slugs:
            return queryset
        return queryset.filter(topics__slug__in=slugs).distinct()
