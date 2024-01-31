"""
Views for collections API
"""
from rest_framework import (
    viewsets,
    mixins,
)
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import (
    Collection,
    Tag,
)
from collection import serializers


class CollectionViewSet(viewsets.ModelViewSet):
    """View to manage collection API"""
    serializer_class = serializers.CollectionDetailSerializer
    queryset = Collection.objects.all()
    authentication_clases = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve collections for the authenitcated user"""
        return self.queryset.filter(user=self.request.user).order_by('-id')

    def get_serializer_class(self):
        """Return the serializer class for request"""
        if self.action == 'list':
            return serializers.CollectionSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new collection"""
        serializer.save(user=self.request.user)


class TagViewSet(mixins.DestroyModelMixin,
                 mixins.UpdateModelMixin,
                 mixins.ListModelMixin,
                 viewsets.GenericViewSet,):
    """Manage tags in the database"""
    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retreieve tags for the authenticated users"""
        return self.queryset.filter(user=self.request.user).order_by('-name')
