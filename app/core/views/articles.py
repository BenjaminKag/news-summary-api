"""
Viewset for articles.
"""
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

from django_filters.rest_framework import DjangoFilterBackend
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from rest_framework.filters import OrderingFilter

from core.models import Article, Summary
from core.serializers import ArticleSerializer, SummarySerializer
from core.filters import ArticleFilter
from core.pagination import DefaultPagination


@method_decorator(cache_page(60*5), name='list')
class ArticleViewSet(ReadOnlyModelViewSet):
    """
    Endpoints:
      GET /api/articles
      GET /api/articles/{id}
      GET /api/articles/{id}/summary
    """
    queryset = Article.objects.all().distinct()
    serializer_class = ArticleSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = ArticleFilter
    ordering_fields = ["published_at"]
    ordering = ["-published_at"]
    pagination_class = DefaultPagination

    @action(detail=True,
            methods=["get"],
            url_path="summary",
            url_name="summary"
            )
    def summary(self, request, pk=None):
        """Fetch a summary of a specific article (read-only)."""
        try:
            summary = Summary.objects.get(article_id=pk)
        except Summary.DoesNotExist:
            return Response(
                {"detail": "Not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = SummarySerializer(summary)
        return Response(serializer.data)
