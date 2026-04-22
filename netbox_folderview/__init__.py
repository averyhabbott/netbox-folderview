from netbox.plugins import PluginConfig


class FolderViewConfig(PluginConfig):
    name = 'netbox_folderview'
    verbose_name = 'FolderView'
    description = 'Folder-tree view of IP prefixes'
    version = '0.1.0'
    base_url = 'folderview'
    min_version = '4.5.0'


config = FolderViewConfig
