"""
Views for collections API
"""
from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiParameter,
    OpenApiTypes,
)
from rest_framework import (
    viewsets,
    mixins,
    status,
)
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response

from core.models import (
    Collection,
    Tag,
    Garment,
)
from collection import serializers


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'tags',
                OpenApiTypes.STR,
                description='Comma separated list of ids to filter',
            ),
            OpenApiParameter(
                'garments',
                OpenApiTypes.STR,
                description='Comma separated list of garment ids to filter',
            )
        ]
    )
)
class CollectionViewSet(viewsets.ModelViewSet):
    """View to manage collection API"""

    serializer_class = serializers.CollectionDetailSerializer
    queryset = Collection.objects.all()
    authentication_clases = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def _params_to_ints(self, qs):
        """Convert a list of strings to integers"""
        return [int(str_id) for str_id in qs.split(',')]

    def get_queryset(self):
        """Retrieve collections for the authenitcated user"""
        tags = self.request.query_params.get('tags')
        garments = self.request.query_params.get('garments')
        queryset = self.queryset
        if tags:
            tag_ids = self._params_to_ints(tags)
            queryset = queryset.filter(tags__id__in=tag_ids)
        if garments:
            garment_ids = self._params_to_ints(garments)
            queryset = queryset.filter(garments__id__in=garment_ids)

        return queryset.filter(
            user=self.request.user
        ).order_by("-id").distinct()

    def get_serializer_class(self):
        """Return the serializer class for request"""
        if self.action == "list":
            return serializers.CollectionSerializer
        elif self.action == 'upload_image':
            return serializers.CollectionImageSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new collection"""
        serializer.save(user=self.request.user)

    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, pk=None):
        """Upload an image to a collection"""
        collection = self.get_object()
        serializer = self.get_serializer(collection, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'assigned_only',
                OpenApiTypes.INT,
                enum=[0, 1],
                description='Filter by items assigned to collections',
            )
        ]
    )
)
class BaseCollectionAttrViewSet(
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """Base viewset for collection attributes"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retreieve tags for the authenticated users"""
        assigned_only = bool(
            int(self.request.query_params.get('assigned_only', 0))
        )
        queryset = self.queryset
        if assigned_only:
            queryset = queryset.filter(collection__isnull=False)

        return queryset.filter(
            user=self.request.user
        ).order_by("-name").distinct()


class TagViewSet(BaseCollectionAttrViewSet):
    """Manage tags in the database"""

    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()


class GarmentViewSet(BaseCollectionAttrViewSet):
    """Manage garments in the database"""

    serializer_class = serializers.GarmentSerializer
    queryset = Garment.objects.all()

    def get_serializer_class(self):
        if self.action == 'upload_image':
            return serializers.GarmentImageSerializer

        return self.serializer_class

    @action(methods=["POST"], detail=True, url_path="upload-image")
    def upload_image(self, request, pk=None):
        """Upload an image to a collection"""
        garment = self.get_object()
        serializer = self.get_serializer(garment, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
