from netbox.plugins import PluginConfig


class FolderViewConfig(PluginConfig):
    name = 'netbox_folderview'
    verbose_name = 'FolderView'
    description = 'Folder-tree view of IP prefixes and user-defined catalogs'
    version = '0.1.3'
    author = 'Avery Abbott'
    base_url = 'folderview'
    min_version = '4.5.0'
    default_auto_field = 'django.db.models.BigAutoField'


config = FolderViewConfig
