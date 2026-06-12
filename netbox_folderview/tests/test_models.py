from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from extras.models import SavedFilter
from ipam.models import Prefix

from netbox_folderview.models import Catalog, Folder, FolderMembership


def _prefix_ct():
    return ContentType.objects.get_for_model(Prefix)


class CatalogTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.prefix_ct = _prefix_ct()
        cls.catalog = Catalog.objects.create(
            name='Devices Catalog',
            object_type=cls.prefix_ct,
            description='A catalog of prefixes',
        )

    def test_str(self):
        self.assertEqual(str(self.catalog), 'Devices Catalog')

    def test_get_absolute_url(self):
        self.assertEqual(
            self.catalog.get_absolute_url(),
            f'/plugins/folderview/catalogs/{self.catalog.pk}/',
        )

    def test_object_type_display(self):
        # Mirrors Catalog.object_type_display: model verbose_name_plural, title-cased.
        self.assertEqual(
            self.catalog.object_type_display,
            Prefix._meta.verbose_name_plural.title(),
        )

    def test_clean_accepts_supported_object_type(self):
        # ipam.prefix resolves to a table + filter form, so clean() should pass.
        catalog = Catalog(name='Valid', object_type=self.prefix_ct)
        catalog.clean()  # should not raise

    def test_clean_rejects_unsupported_object_type(self):
        # contenttypes is an excluded app; get_config_for_type() returns None.
        unsupported_ct = ContentType.objects.get_for_model(ContentType)
        catalog = Catalog(name='Invalid', object_type=unsupported_ct)
        with self.assertRaises(ValidationError) as ctx:
            catalog.clean()
        self.assertIn('object_type', ctx.exception.message_dict)

    def test_name_validator_rejects_invalid_characters(self):
        catalog = Catalog(name='Bad@Name!', object_type=self.prefix_ct)
        with self.assertRaises(ValidationError) as ctx:
            catalog.full_clean()
        self.assertIn('name', ctx.exception.message_dict)

    def test_name_validator_accepts_allowed_characters(self):
        catalog = Catalog(name='Good-Name_1 2', object_type=self.prefix_ct)
        catalog.full_clean()  # should not raise


class FolderTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.prefix_ct = _prefix_ct()
        cls.catalog = Catalog.objects.create(name='Catalog A', object_type=cls.prefix_ct)
        cls.other_catalog = Catalog.objects.create(name='Catalog B', object_type=cls.prefix_ct)

        # A shared SavedFilter that applies to the catalog's object type (prefixes).
        cls.saved_filter = SavedFilter.objects.create(
            name='Prefix Filter',
            slug='prefix-filter',
            shared=True,
            parameters={'status': ['active']},
        )
        cls.saved_filter.object_types.set([cls.prefix_ct])

        # A SavedFilter that does NOT apply to prefixes.
        cls.foreign_filter = SavedFilter.objects.create(
            name='Other Filter',
            slug='other-filter',
            shared=True,
            parameters={},
        )
        cls.foreign_filter.object_types.set([ContentType.objects.get_for_model(ContentType)])

        cls.static_parent = Folder.objects.create(
            name='Static Parent', catalog=cls.catalog, folder_type=Folder.STATIC,
        )
        cls.dynamic_parent = Folder.objects.create(
            name='Dynamic Parent', catalog=cls.catalog, folder_type=Folder.DYNAMIC,
            saved_filter=cls.saved_filter,
        )

    def test_str(self):
        self.assertEqual(str(self.static_parent), 'Static Parent')

    def test_get_absolute_url(self):
        self.assertEqual(
            self.static_parent.get_absolute_url(),
            f'/plugins/folderview/folders/{self.static_parent.pk}/',
        )

    def test_clean_valid_static_folder(self):
        folder = Folder(
            name='Child', catalog=self.catalog, parent=self.static_parent,
            folder_type=Folder.STATIC,
        )
        folder.clean()  # should not raise

    def test_clean_valid_dynamic_folder(self):
        folder = Folder(
            name='Dyn', catalog=self.catalog, folder_type=Folder.DYNAMIC,
            saved_filter=self.saved_filter,
        )
        folder.clean()  # should not raise

    def test_clean_parent_must_share_catalog(self):
        folder = Folder(
            name='Child', catalog=self.catalog, parent=None, folder_type=Folder.STATIC,
        )
        # Parent belongs to a different catalog.
        other_parent = Folder.objects.create(
            name='Other Parent', catalog=self.other_catalog, folder_type=Folder.STATIC,
        )
        folder.parent = other_parent
        with self.assertRaises(ValidationError) as ctx:
            folder.clean()
        self.assertIn('parent', ctx.exception.message_dict)

    def test_clean_static_cannot_nest_under_dynamic(self):
        folder = Folder(
            name='Static Child', catalog=self.catalog, parent=self.dynamic_parent,
            folder_type=Folder.STATIC,
        )
        with self.assertRaises(ValidationError) as ctx:
            folder.clean()
        self.assertIn('parent', ctx.exception.message_dict)

    def test_clean_dynamic_requires_saved_filter(self):
        folder = Folder(
            name='Dyn No Filter', catalog=self.catalog, folder_type=Folder.DYNAMIC,
            saved_filter=None,
        )
        with self.assertRaises(ValidationError) as ctx:
            folder.clean()
        self.assertIn('saved_filter', ctx.exception.message_dict)

    def test_clean_dynamic_saved_filter_must_cover_object_type(self):
        folder = Folder(
            name='Dyn Wrong Filter', catalog=self.catalog, folder_type=Folder.DYNAMIC,
            saved_filter=self.foreign_filter,
        )
        with self.assertRaises(ValidationError) as ctx:
            folder.clean()
        self.assertIn('saved_filter', ctx.exception.message_dict)

    def test_clean_static_cannot_have_saved_filter(self):
        folder = Folder(
            name='Static With Filter', catalog=self.catalog, folder_type=Folder.STATIC,
            saved_filter=self.saved_filter,
        )
        with self.assertRaises(ValidationError) as ctx:
            folder.clean()
        self.assertIn('saved_filter', ctx.exception.message_dict)


class FolderMembershipTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        catalog = Catalog.objects.create(name='Catalog', object_type=_prefix_ct())
        cls.folder = Folder.objects.create(
            name='Folder', catalog=catalog, folder_type=Folder.STATIC,
        )

    def test_str(self):
        membership = FolderMembership.objects.create(folder=self.folder, object_id=42)
        self.assertEqual(str(membership), f'{self.folder} – 42')

    def test_unique_constraint(self):
        FolderMembership.objects.create(folder=self.folder, object_id=1)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                FolderMembership.objects.create(folder=self.folder, object_id=1)

    def test_same_object_in_different_folders_allowed(self):
        catalog = self.folder.catalog
        other_folder = Folder.objects.create(
            name='Other', catalog=catalog, folder_type=Folder.STATIC,
        )
        FolderMembership.objects.create(folder=self.folder, object_id=7)
        # Same object_id, different folder → no constraint violation.
        FolderMembership.objects.create(folder=other_folder, object_id=7)
        self.assertEqual(FolderMembership.objects.filter(object_id=7).count(), 2)
