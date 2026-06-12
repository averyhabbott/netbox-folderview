from netbox.api.viewsets import NetBoxModelViewSet

from ..filtersets import CatalogFilterSet, FolderFilterSet
from ..models import Catalog, Folder
from .serializers import CatalogSerializer, FolderSerializer

__all__ = ('CatalogViewSet', 'FolderViewSet')


class CatalogViewSet(NetBoxModelViewSet):
    queryset = Catalog.objects.select_related('object_type').prefetch_related('tags')
    serializer_class = CatalogSerializer
    filterset_class = CatalogFilterSet


class FolderViewSet(NetBoxModelViewSet):
    queryset = Folder.objects.select_related('catalog', 'parent', 'saved_filter').prefetch_related('tags')
    serializer_class = FolderSerializer
    filterset_class = FolderFilterSet
