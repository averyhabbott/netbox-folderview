from django.test import TestCase

from ipam.filtersets import PrefixFilterSet
from ipam.forms import PrefixFilterForm
from ipam.models import Prefix
from ipam.tables import PrefixTable

from netbox_folderview.catalog_config import get_catalog_type_queryset, get_config_for_type


class GetConfigForTypeTestCase(TestCase):

    def test_supported_type_resolves(self):
        config = get_config_for_type('ipam.prefix')
        self.assertIsNotNone(config)
        self.assertEqual(config['model'], Prefix)
        self.assertEqual(config['table'], PrefixTable)
        self.assertEqual(config['filterset'], PrefixFilterSet)
        self.assertEqual(config['filterset_form'], PrefixFilterForm)

    def test_excluded_app_returns_none(self):
        # The plugin's own models and core/auth apps must never be catalog types.
        self.assertIsNone(get_config_for_type('netbox_folderview.catalog'))
        self.assertIsNone(get_config_for_type('users.user'))

    def test_unregistered_type_returns_none(self):
        self.assertIsNone(get_config_for_type('nonexistent.model'))


class GetCatalogTypeQuerysetTestCase(TestCase):

    def test_queryset_is_nonempty(self):
        self.assertTrue(get_catalog_type_queryset().exists())

    def test_queryset_excludes_excluded_apps(self):
        excluded = {'netbox_folderview', 'core', 'users', 'auth', 'contenttypes', 'sessions'}
        app_labels = set(
            get_catalog_type_queryset().values_list('app_label', flat=True)
        )
        self.assertFalse(app_labels & excluded)

    def test_every_returned_type_is_resolvable(self):
        for ct in get_catalog_type_queryset():
            self.assertIsNotNone(get_config_for_type(f'{ct.app_label}.{ct.model}'))

    def test_includes_prefix(self):
        labels = {
            f'{ct.app_label}.{ct.model}'
            for ct in get_catalog_type_queryset()
        }
        self.assertIn('ipam.prefix', labels)
