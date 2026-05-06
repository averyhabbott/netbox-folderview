from django.apps import apps
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from netbox.navigation import MenuGroup
from netbox.plugins.navigation import PluginMenu, PluginMenuButton, PluginMenuItem

manage_catalogs_item = PluginMenuItem(
    link='plugins:netbox_folderview:catalog_list',
    link_text=_('Manage Catalogs'),
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_folderview:catalog_add',
            title=_('Add'),
            icon_class='mdi mdi-plus-thick',
        ),
    ),
    permissions=['netbox_folderview.view_catalog'],
)

prefix_tree_item = PluginMenuItem(
    link='plugins:netbox_folderview:prefix_tree',
    link_text=_('Prefix Tree'),
)


class CatalogMenuItems:
    def __iter__(self):
        Catalog = apps.get_model('netbox_folderview', 'Catalog')
        for catalog in Catalog.objects.order_by('name'):
            item = PluginMenuItem(
                link=None,
                link_text=catalog.name,
                permissions=['netbox_folderview.view_catalog'],
            )
            item.url = reverse_lazy(
                'plugins:netbox_folderview:catalog',
                kwargs={'pk': catalog.pk},
            )
            yield item


def get_groups():
    return [
        (_('IPAM'), (prefix_tree_item,)),
        (_('MANAGE'), (manage_catalogs_item,)),
        (_('CATALOGS'), CatalogMenuItems()),
    ]


class _DynamicPluginMenu(PluginMenu):
    def __init__(self, label, groups_fn, icon_class=None):
        self.label = label
        self._groups_fn = groups_fn
        if icon_class is not None:
            self.icon_class = icon_class

    @property
    def groups(self):
        return [MenuGroup(label, items) for label, items in self._groups_fn()]


menu = _DynamicPluginMenu(
    label=_('FolderView'),
    groups_fn=get_groups,
    icon_class='mdi mdi-folder-network',
)
