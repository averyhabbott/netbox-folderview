from django.apps import apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase
from packaging import version

from core.models import ObjectType
from netbox.plugins.navigation import PluginMenu
from netbox.registry import registry

from netbox_folderview import config as folderview_config


class PluginConfigTestCase(TestCase):

    def test_plugin_installed(self):
        self.assertTrue(apps.is_installed('netbox_folderview'))

    def test_model_registration(self):
        for model in ('catalog', 'folder', 'foldermembership'):
            with self.subTest(model=model):
                self.assertTrue(
                    ObjectType.objects.filter(app_label='netbox_folderview', model=model).exists()
                )

    def test_menu_registered(self):
        menus = registry['plugins']['menus']
        folderview_menus = [m for m in menus if getattr(m, 'label', None) == 'FolderView']
        self.assertEqual(len(folderview_menus), 1)
        menu = folderview_menus[0]
        self.assertIsInstance(menu, PluginMenu)
        # IPAM, MANAGE, CATALOGS groups are all present.
        self.assertEqual(len(menu.groups), 3)


class CompatibilityTestCase(TestCase):
    """
    Validates the plugin's declared NetBox version range and confirms the
    environment under test (NetBox 4.6.x) falls within it.
    """

    def test_min_version_enforced(self):
        with self.assertRaises(ImproperlyConfigured):
            folderview_config.validate({}, '4.4.0')

    def test_max_version_enforced(self):
        with self.assertRaises(ImproperlyConfigured):
            folderview_config.validate({}, '5.0.0')

    def test_supported_version_passes(self):
        # An explicit 4.6.x version must validate cleanly.
        folderview_config.validate({}, '4.6.0')

    def test_running_version_within_declared_range(self):
        current = version.parse(settings.RELEASE.version)
        self.assertGreaterEqual(current, version.parse(folderview_config.min_version))
        self.assertLessEqual(current, version.parse(folderview_config.max_version))

    def test_running_version_validates(self):
        # The actual running NetBox version must satisfy the plugin's constraints.
        folderview_config.validate({}, settings.RELEASE.version)
