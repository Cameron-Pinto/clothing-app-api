"""
Serializers for collection API
"""
from rest_framework import serializers

from core.models import (
    Collection,
    Tag,
    Garment,
)


class GarmentSerializer(serializers.ModelSerializer):
    """Serializer for garments"""

    class Meta:
        model = Garment
        fields = [
            "id",
            "name",
        ]
        read_only_fields = ["id"]


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tags"""

    class Meta:
        model = Tag
        fields = ["id", "name"]
        read_only_fields = ["id"]


class CollectionSerializer(serializers.ModelSerializer):
    """Serializer for collections"""

    tags = TagSerializer(many=True, required=False)
    garments = GarmentSerializer(many=True, required=False)

    class Meta:
        model = Collection
        fields = ["id", "title", "link", "tags", "garments"]
        read_only_fields = ["id"]

    def _get_or_create_tags(self, tags, collection):
        """Handle getting or creating tags as needed"""
        auth_user = self.context["request"].user
        for tag in tags:
            tag_obj, create = Tag.objects.get_or_create(
                user=auth_user,
                **tag,
            )
            collection.tags.add(tag_obj)

    def _get_or_create_garments(self, garments, collection):
        """Handle gettings or creating garments as needed"""
        auth_user = self.context["request"].user
        for garment in garments:
            garment_obj, create = Garment.objects.get_or_create(
                user=auth_user,
                **garment,
            )
            collection.garments.add(garment_obj)

    def create(self, validated_data):
        """Create a collection"""
        tags = validated_data.pop("tags", [])
        garments = validated_data.pop("garments", [])
        collection = Collection.objects.create(**validated_data)
        self._get_or_create_tags(tags, collection)
        self._get_or_create_garments(garments, collection)

        return collection

    def update(self, instance, validated_data):
        """Update collection"""
        tags = validated_data.pop("tags", None)
        garments = validated_data.pop("garments", None)
        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)

        elif garments is not None:
            instance.garments.clear()
            self._get_or_create_garments(garments, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class CollectionDetailSerializer(CollectionSerializer):
    """Serializer for collection details view"""

    class Meta(CollectionSerializer.Meta):
        fields = CollectionSerializer.Meta.fields + ["description"]


class CollectionImageSerializer(serializers.ModelSerializer):
    """Serializer for upload images to collection"""

    class Meta:
        model = Collection
        fields = ['id', 'image']
        read_only_fields = ['id']
        extra_kwargs = {'image': {'required': 'True'}}


class GarmentImageSerializer(serializers.ModelSerializer):
    """Serializer for uploading imaged for a garment"""

    class Meta:
        model = Garment
        fields = ['id', 'image']
        read_only_fields = ['id']
        extra_kwargs = {'image': {'required': 'True'}}
