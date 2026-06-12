from netbox.plugins import PluginConfig

__version__ = '0.3.0'


class FolderViewConfig(PluginConfig):
    name = 'netbox_folderview'
    verbose_name = 'FolderView'
    description = 'Folder-tree view of IP prefixes and user-defined catalogs'
    version = __version__
    author = 'Avery Abbott'
    author_email = 'averyhabbott@yahoo.com'
    base_url = 'folderview'
    min_version = '4.5.0'
    max_version = '4.6.999'
    default_auto_field = 'django.db.models.BigAutoField'


config = FolderViewConfig
