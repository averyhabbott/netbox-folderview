import django_tables2 as tables
from django.utils.translation import gettext_lazy as _

from ipam.models import IPAddress, Prefix
from netbox.tables import NetBoxTable, columns

__all__ = ('PrefixIPTable', 'PrefixTreeTable')


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
