from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from ipam.models import Prefix
from tenancy.models import Tenant

from netbox_folderview.filtersets import CatalogFilterSet, FolderFilterSet
from netbox_folderview.models import Catalog, Folder


class CatalogFilterSetTestCase(TestCase):
    queryset = Catalog.objects.all()
    filterset = CatalogFilterSet

    @classmethod
    def setUpTestData(cls):
        prefix_ct = ContentType.objects.get_for_model(Prefix)
        tenant_ct = ContentType.objects.get_for_model(Tenant)

        Catalog.objects.bulk_create([
            Catalog(name='Network Devices', object_type=prefix_ct,
                    description='primary', allow_duplicates=True),
            Catalog(name='Network Prefixes', object_type=prefix_ct,
                    description='secondary', allow_duplicates=False),
            Catalog(name='Tenants', object_type=tenant_ct,
                    description='tenant catalog', allow_duplicates=True),
        ])

    def test_name(self):
        params = {'name': 'network'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_allow_duplicates(self):
        params = {'allow_duplicates': False}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_object_type(self):
        prefix_ct = ContentType.objects.get_for_model(Prefix)
        # object_type is an auto-generated ModelChoiceFilter (single value).
        params = {'object_type': prefix_ct.pk}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_search_name_and_description(self):
        self.assertEqual(self.filterset({'q': 'Prefixes'}, self.queryset).qs.count(), 1)
        self.assertEqual(self.filterset({'q': 'tenant catalog'}, self.queryset).qs.count(), 1)
        self.assertEqual(self.filterset({'q': ''}, self.queryset).qs.count(), 3)


class FolderFilterSetTestCase(TestCase):
    queryset = Folder.objects.all()
    filterset = FolderFilterSet

    @classmethod
    def setUpTestData(cls):
        prefix_ct = ContentType.objects.get_for_model(Prefix)
        cls.catalog_a = Catalog.objects.create(name='Catalog A', object_type=prefix_ct)
        cls.catalog_b = Catalog.objects.create(name='Catalog B', object_type=prefix_ct)

        Folder.objects.create(
            name='Static One', catalog=cls.catalog_a, folder_type=Folder.STATIC,
            show_nested_objects=True,
        )
        Folder.objects.create(
            name='Static Two', catalog=cls.catalog_a, folder_type=Folder.STATIC,
            show_nested_objects=False,
        )
        Folder.objects.create(
            name='Other Folder', catalog=cls.catalog_b, folder_type=Folder.STATIC,
            show_nested_objects=True,
        )

    def test_name(self):
        self.assertEqual(self.filterset({'name': 'static'}, self.queryset).qs.count(), 2)

    def test_catalog(self):
        # catalog is an auto-generated ModelChoiceFilter (single value).
        params = {'catalog': self.catalog_a.pk}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_folder_type(self):
        params = {'folder_type': Folder.STATIC}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)

    def test_show_nested_objects(self):
        params = {'show_nested_objects': True}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_search(self):
        self.assertEqual(self.filterset({'q': 'Other'}, self.queryset).qs.count(), 1)
        self.assertEqual(self.filterset({'q': ''}, self.queryset).qs.count(), 3)
