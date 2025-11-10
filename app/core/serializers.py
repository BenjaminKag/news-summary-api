"""
Serializers for the news summary API.
"""
from rest_framework import serializers

from .models import Source, Topic, Summary, Article


class SourceSerializer(serializers.ModelSerializer):
    """Serializer for Source model."""

    class Meta:
        model = Source
        fields = ['id', 'name', 'slug', 'homepage']
        read_only_fields = ['id', 'slug']


class TopicSerializer(serializers.ModelSerializer):
    """Serializer for Topic model."""

    class Meta:
        model = Topic
        fields = ['id', 'name', 'slug']
        read_only_fields = ['id', 'slug']


class SummarySerializer(serializers.ModelSerializer):
    """Serializer for Summary model."""

    class Meta:
        model = Summary
        fields = ['text', 'model_name']
        read_only_fields = ['text', 'model_name']

    def to_internal_value(self, data):
        # Make the serializer read-only by preventing any
        # input data from being accepted.
        raise serializers.ValidationError({
            "text": ["Summary is read-only."],
            "model_name": ["Summary is read-only."],
        })


class ArticleSerializer(serializers.ModelSerializer):
    source = SourceSerializer(read_only=True)
    source_id = serializers.PrimaryKeyRelatedField(
        queryset=Source.objects.all(),
        write_only=True,
        source="source"
    )

    topics = TopicSerializer(many=True, read_only=True)
    topic_ids = serializers.PrimaryKeyRelatedField(
        queryset=Topic.objects.all(),
        many=True,
        write_only=True,
        source="topics",
        required=False
    )

    summary = SummarySerializer(read_only=True)

    class Meta:
        model = Article
        fields = [
            "id",
            "title",
            "url",
            "source", "source_id",
            "topics", "topic_ids",
            "summary",
            "published_at",
            "author",
            "content",
        ]
        read_only_fields = ["id", "summary"]
