from netbox.plugins.navigation import PluginMenu, PluginMenuItem

menu = PluginMenu(
    label='FolderView',
    groups=(
        ('IP Management', (
            PluginMenuItem(
                link='plugins:netbox_folderview:prefix_tree',
                link_text='Prefix Tree',
            ),
        )),
    ),
    icon_class='mdi mdi-folder-network',
)
