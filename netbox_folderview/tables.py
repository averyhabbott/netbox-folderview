import django_tables2 as tables
from django.utils.translation import gettext_lazy as _

from ipam.models import IPAddress, Prefix
from netbox.tables import NetBoxTable, columns

from .models import Catalog, Folder

__all__ = ('CatalogTable', 'FolderTable', 'PrefixIPTable', 'PrefixTreeTable')

CATALOG_EXTRA_BUTTONS = """
{% load i18n %}
<a href="{% url 'plugins:netbox_folderview:catalog_duplicates' pk=record.pk %}"
   class="btn btn-sm btn-outline-secondary"
   title="{% trans 'Find Duplicate Objects' %}">
  <i class="mdi mdi-content-duplicate"></i>
</a>
"""


class CatalogTable(NetBoxTable):
    name = tables.Column(linkify=True, verbose_name=_('Name'))
    object_type = tables.Column(verbose_name=_('Object Type'))
    folder_count = tables.Column(verbose_name=_('Folders'), orderable=False)
    allow_duplicates = columns.BooleanColumn(verbose_name=_('Allow Duplicates'))
    actions = columns.ActionsColumn(extra_buttons=CATALOG_EXTRA_BUTTONS)

    class Meta(NetBoxTable.Meta):
        model = Catalog
        fields = ('pk', 'id', 'name', 'object_type', 'description', 'folder_count', 'allow_duplicates', 'actions')
        default_columns = ('pk', 'name', 'object_type', 'folder_count', 'allow_duplicates', 'actions')

    def render_object_type(self, value):
        model_class = value.model_class()
        if model_class:
            return model_class._meta.verbose_name_plural.title()
        return str(value)


class FolderTable(NetBoxTable):
    name = tables.Column(verbose_name=_('Name'))
    folder_type = tables.Column(verbose_name=_('Type'))
    parent = tables.Column(verbose_name=_('Parent'))
    show_nested_objects = columns.BooleanColumn(verbose_name=_('Show Nested'))

    class Meta(NetBoxTable.Meta):
        model = Folder
        fields = ('pk', 'id', 'name', 'folder_type', 'parent', 'show_nested_objects', 'actions')
        default_columns = ('pk', 'name', 'folder_type', 'parent', 'show_nested_objects', 'actions')


class PrefixTreeTable(NetBoxTable):
    prefix = tables.Column(
        verbose_name=_('Prefix'),
        linkify=True,
        attrs={'td': {'class': 'text-nowrap font-monospace'}},
    )
    description = tables.Column(verbose_name=_('Description'))
    status = columns.ChoiceFieldColumn(verbose_name=_('Status'))
    vrf = tables.Column(verbose_name=_('VRF'), linkify=True)
    role = tables.Column(verbose_name=_('Role'), linkify=True)
    tenant = tables.Column(verbose_name=_('Tenant'), linkify=True)

    class Meta(NetBoxTable.Meta):
        model = Prefix
        fields = ('prefix', 'description', 'status', 'vrf', 'role', 'tenant')
        default_columns = ('prefix', 'description')
        row_attrs = {
            'data-pk': lambda record: record.pk,
            'ondblclick': lambda record: f"window.location.href='{record.get_absolute_url()}'",
            'style': 'cursor: pointer;',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'pk' in self.base_columns:
            self.columns.hide('pk')
        if 'actions' in self.base_columns:
            self.columns.hide('actions')


class PrefixIPTable(NetBoxTable):
    address = tables.Column(verbose_name=_('IP Address'), linkify=True)
    status = columns.ChoiceFieldColumn(verbose_name=_('Status'))
    dns_name = tables.Column(verbose_name=_('DNS Name'))
    description = tables.Column(verbose_name=_('Description'))
    vrf = tables.Column(verbose_name=_('VRF'), linkify=True)
    tenant = tables.Column(verbose_name=_('Tenant'), linkify=True)

    class Meta(NetBoxTable.Meta):
        model = IPAddress
        fields = ('address', 'status', 'dns_name', 'description', 'vrf', 'tenant')
        default_columns = ('address', 'status', 'dns_name', 'description')
        row_attrs = {
            'data-pk': lambda record: record.pk,
            'ondblclick': lambda record: f"window.location.href='{record.get_absolute_url()}'",
            'style': 'cursor: pointer;',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'pk' in self.base_columns:
            self.columns.hide('pk')
        if 'actions' in self.base_columns:
            self.columns.hide('actions')
