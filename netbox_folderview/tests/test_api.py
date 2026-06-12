from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from ipam.models import Prefix
from utilities.testing import APITestCase, APIViewTestCases

from netbox_folderview.models import Catalog, Folder


def _prefix_ct():
    return ContentType.objects.get_for_model(Prefix)


class AppTest(APITestCase):

    def test_root(self):
        url = reverse('plugins-api:netbox_folderview-api:api-root')
        response = self.client.get(f'{url}?format=api', **self.header)
        self.assertEqual(response.status_code, 200)


class CatalogTest(
    APIViewTestCases.GetObjectViewTestCase,
    APIViewTestCases.ListObjectsViewTestCase,
    APIViewTestCases.CreateObjectViewTestCase,
    APIViewTestCases.UpdateObjectViewTestCase,
    APIViewTestCases.DeleteObjectViewTestCase,
):
    model = Catalog
    view_namespace = 'plugins-api:netbox_folderview'
    brief_fields = ['description', 'display', 'id', 'name', 'url']
    bulk_update_data = {
        'description': 'Updated description',
    }

    @classmethod
    def setUpTestData(cls):
        prefix_ct = _prefix_ct()
        Catalog.objects.bulk_create([
            Catalog(name='Catalog 1', object_type=prefix_ct),
            Catalog(name='Catalog 2', object_type=prefix_ct),
            Catalog(name='Catalog 3', object_type=prefix_ct),
        ])
        cls.create_data = [
            {'name': 'Catalog 4', 'object_type': 'ipam.prefix', 'description': 'four'},
            {'name': 'Catalog 5', 'object_type': 'ipam.prefix', 'description': 'five'},
            {'name': 'Catalog 6', 'object_type': 'ipam.prefix', 'description': 'six'},
        ]


class FolderTest(
    APIViewTestCases.GetObjectViewTestCase,
    APIViewTestCases.ListObjectsViewTestCase,
    APIViewTestCases.CreateObjectViewTestCase,
    APIViewTestCases.UpdateObjectViewTestCase,
    APIViewTestCases.DeleteObjectViewTestCase,
):
    model = Folder
    view_namespace = 'plugins-api:netbox_folderview'
    brief_fields = ['display', 'id', 'name', 'url']
    bulk_update_data = {
        'show_nested_objects': False,
    }

    @classmethod
    def setUpTestData(cls):
        catalog = Catalog.objects.create(name='Catalog', object_type=_prefix_ct())
        Folder.objects.bulk_create([
            Folder(name='Folder 1', catalog=catalog, folder_type=Folder.STATIC),
            Folder(name='Folder 2', catalog=catalog, folder_type=Folder.STATIC),
            Folder(name='Folder 3', catalog=catalog, folder_type=Folder.STATIC),
        ])
        cls.create_data = [
            {'name': 'Folder 4', 'catalog': catalog.pk, 'folder_type': Folder.STATIC},
            {'name': 'Folder 5', 'catalog': catalog.pk, 'folder_type': Folder.STATIC},
            {'name': 'Folder 6', 'catalog': catalog.pk, 'folder_type': Folder.STATIC},
        ]
