"""
Serializers for collection API
"""
from rest_framework import serializers

from core.models import Collection


class CollectionSerializer(serializers.ModelSerializer):
    """Serializer for collections"""

    class Meta:
        model = Collection
        fields = ['id', 'title', 'link']
        read_only_fields = ['id']


class CollectionDetailSerializer(CollectionSerializer):
    """Serializer for collection details view"""

    class Meta(CollectionSerializer.Meta):
        fields = CollectionSerializer.Meta.fields + ['description']
