"""
Views for collections API
"""
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Collection
from collection import serializers


class CollectionViewSet(viewsets.ModelViewSet):
    """View to manage collection API"""
    serializer_class = serializers.CollectionDetailSerializer
    queryset = Collection.objects.all()
    authentication_clases = [TokenAuthentication]
    persmission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve collectiosn for the authenitcated user"""
        return self.queryset.filter(user=self.request.user.id).order_by('-id')

    def get_serializer_class(self):
        """Return the serializer class for request"""
        if self.action == 'list':
            return serializers.CollectionSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new collection"""
        serializer.save(user=self.request.user)
