"""
Serializers for collection API
"""
from rest_framework import serializers

from core.models import (
    Collection,
    Tag,
)


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tags"""

    class Meta:
        model = Tag
        fields = ["id", "name"]
        read_only_fields = ["id"]


class CollectionSerializer(serializers.ModelSerializer):
    """Serializer for collections"""

    tags = TagSerializer(many=True, required=False)

    class Meta:
        model = Collection
        fields = ["id", "title", "link", "tags"]
        read_only_fields = ["id"]

    def _get_or_create_tags(self, tags, collection):
        """Handle getting or creating tags as needed"""
        auth_user = self.context["request"].user
        for tag in tags:
            tag_obj, created = Tag.objects.get_or_create(
                user=auth_user,
                **tag,
            )
            collection.tags.add(tag_obj)

    def create(self, validated_data):
        """Create a collection"""
        tags = validated_data.pop("tags", [])
        collection = Collection.objects.create(**validated_data)
        self._get_or_create_tags(tags, collection)

        return collection

    def update(self, instance, validated_data):
        """Update collection"""
        tags = validated_data.pop("tags", None)
        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class CollectionDetailSerializer(CollectionSerializer):
    """Serializer for collection details view"""

    class Meta(CollectionSerializer.Meta):
        fields = CollectionSerializer.Meta.fields + ["description"]
