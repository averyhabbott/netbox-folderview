from core.models import ObjectType
from netbox.api.fields import ContentTypeField
from netbox.api.serializers import NetBoxModelSerializer

from ..models import Catalog, Folder

__all__ = ('CatalogSerializer', 'FolderSerializer')


class CatalogSerializer(NetBoxModelSerializer):
    object_type = ContentTypeField(queryset=ObjectType.objects.all())

    class Meta:
        model = Catalog
        fields = (
            'id', 'url', 'display', 'name', 'object_type', 'description',
            'allow_duplicates', 'default_show_nested_objects', 'tags',
            'custom_fields', 'created', 'last_updated',
        )
        brief_fields = ('id', 'url', 'display', 'name', 'description')


class FolderSerializer(NetBoxModelSerializer):
    catalog = CatalogSerializer(nested=True)

    class Meta:
        model = Folder
        fields = (
            'id', 'url', 'display', 'name', 'catalog', 'parent', 'folder_type',
            'show_nested_objects', 'saved_filter', 'tags',
            'custom_fields', 'created', 'last_updated',
        )
        brief_fields = ('id', 'url', 'display', 'name')
