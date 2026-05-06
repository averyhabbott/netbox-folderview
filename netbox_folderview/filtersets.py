import django_filters
from django.db.models import Q
from ipam.filtersets import PrefixFilterSet
from netbox.filtersets import NetBoxModelFilterSet
from utilities.filtersets import register_filterset

from .models import Catalog, Folder

__all__ = ('CatalogFilterSet', 'FolderFilterSet', 'FolderViewPrefixFilterSet')


class FolderViewPrefixFilterSet(PrefixFilterSet):
    pass


@register_filterset
class CatalogFilterSet(NetBoxModelFilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Catalog
        fields = ('name', 'allow_duplicates', 'object_type')

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value)
        )


@register_filterset
class FolderFilterSet(NetBoxModelFilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Folder
        fields = ('name', 'catalog', 'folder_type', 'show_nested_objects')

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(name__icontains=value)
