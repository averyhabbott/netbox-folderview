from netbox.plugins.navigation import PluginMenu, PluginMenuItem

menu = PluginMenu(
    label='FolderView',
    groups=(
        ('IPAM', (
            PluginMenuItem(
                link='plugins:netbox_folderview:prefix_tree',
                link_text='Prefix Tree',
            ),
        )),
    ),
    icon_class='mdi mdi-folder-network',
)
