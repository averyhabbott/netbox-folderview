from django.contrib.contenttypes.models import ContentType
from django.test import override_settings
from django.urls import reverse

from core.models import ObjectType
from extras.models import SavedFilter
from ipam.models import Prefix
from users.models import ObjectPermission
from utilities.testing import ModelViewTestCase, TestCase, ViewTestCases, create_tags

from netbox_folderview.models import Catalog, Folder, FolderMembership


def _prefix_ct():
    return ContentType.objects.get_for_model(Prefix)


class FolderViewModelTestCase(ModelViewTestCase):
    """
    Base for the plugin's generic CRUD views. NetBox's ModelViewTestCase resolves
    URLs as ``<app>:<model>_<action>``; plugin URLs live under the ``plugins:``
    namespace, so we prepend it here.
    """
    def _get_base_url(self):
        return f'plugins:{self.model._meta.app_label}:{self.model._meta.model_name}_{{}}'


class CatalogViewTestCase(
    FolderViewModelTestCase,
    ViewTestCases.GetObjectViewTestCase,
    ViewTestCases.GetObjectChangelogViewTestCase,
    ViewTestCases.CreateObjectViewTestCase,
    ViewTestCases.EditObjectViewTestCase,
    ViewTestCases.DeleteObjectViewTestCase,
    ViewTestCases.ListObjectsViewTestCase,
):
    model = Catalog

    @classmethod
    def setUpTestData(cls):
        prefix_ct = _prefix_ct()
        Catalog.objects.bulk_create([
            Catalog(name='Catalog 1', object_type=prefix_ct),
            Catalog(name='Catalog 2', object_type=prefix_ct),
            Catalog(name='Catalog 3', object_type=prefix_ct),
        ])
        tags = create_tags('Alpha', 'Bravo', 'Charlie')

        cls.form_data = {
            'name': 'Catalog X',
            'object_type': prefix_ct.pk,
            'description': 'A new catalog',
            'allow_duplicates': True,
            'default_show_nested_objects': True,
            'tags': [t.pk for t in tags],
        }

    def test_list_objects_with_constrained_permission(self):
        # Override the inherited test: it asserts that a non-permitted object's
        # URL is absent from the *entire* page, but the FolderView nav menu
        # (navigation.CatalogMenuItems) lists every catalog the user can view at
        # the model level, so that URL legitimately appears in the page chrome.
        # We instead assert the list *table* itself honors the object-level
        # constraint, which is what this view is responsible for.
        instance1, instance2 = self._get_queryset().all()[:2]
        obj_perm = ObjectPermission(
            name='Test permission',
            constraints={'pk': instance1.pk},
            actions=['view'],
        )
        obj_perm.save()
        obj_perm.users.add(self.user)
        obj_perm.object_types.add(ObjectType.objects.get_for_model(self.model))

        response = self.client.get(self._get_url('list'))
        self.assertHttpStatus(response, 200)
        table_pks = {row.record.pk for row in response.context['table'].rows}
        self.assertIn(instance1.pk, table_pks)
        self.assertNotIn(instance2.pk, table_pks)


class FolderViewTestCase(
    FolderViewModelTestCase,
    ViewTestCases.GetObjectViewTestCase,
    ViewTestCases.GetObjectChangelogViewTestCase,
    ViewTestCases.CreateObjectViewTestCase,
    ViewTestCases.EditObjectViewTestCase,
    ViewTestCases.DeleteObjectViewTestCase,
):
    model = Folder

    @classmethod
    def setUpTestData(cls):
        catalog = Catalog.objects.create(name='Catalog', object_type=_prefix_ct())
        Folder.objects.bulk_create([
            Folder(name='Folder 1', catalog=catalog, folder_type=Folder.STATIC),
            Folder(name='Folder 2', catalog=catalog, folder_type=Folder.STATIC),
            Folder(name='Folder 3', catalog=catalog, folder_type=Folder.STATIC),
        ])
        tags = create_tags('Alpha', 'Bravo', 'Charlie')

        cls.form_data = {
            'name': 'Folder X',
            'catalog': catalog.pk,
            'folder_type': Folder.STATIC,
            'show_nested_objects': True,
            'tags': [t.pk for t in tags],
        }


@override_settings(LOGIN_REQUIRED=False, EXEMPT_VIEW_PERMISSIONS=['*'])
class CustomViewsTestCase(TestCase):
    """
    Covers the bespoke (non-generic) views: prefix tree, folder objects, and the
    add / remove / move / duplicates operations.
    """

    @classmethod
    def setUpTestData(cls):
        cls.prefix_ct = _prefix_ct()

        cls.catalog = Catalog.objects.create(name='Catalog', object_type=cls.prefix_ct)
        cls.nodup_catalog = Catalog.objects.create(
            name='No Dups', object_type=cls.prefix_ct, allow_duplicates=False,
        )

        # Catalog whose object type cannot be resolved (contenttypes is excluded).
        cls.unsupported_catalog = Catalog.objects.create(
            name='Unsupported',
            object_type=ContentType.objects.get_for_model(ContentType),
        )

        cls.prefix_parent = Prefix.objects.create(prefix='10.0.0.0/16')
        cls.prefix_child = Prefix.objects.create(prefix='10.0.1.0/24')

        # Static folder hierarchy with memberships.
        cls.folder = Folder.objects.create(
            name='Static', catalog=cls.catalog, folder_type=Folder.STATIC,
            show_nested_objects=True,
        )
        cls.child_folder = Folder.objects.create(
            name='Static Child', catalog=cls.catalog, parent=cls.folder,
            folder_type=Folder.STATIC,
        )
        FolderMembership.objects.create(folder=cls.folder, object_id=cls.prefix_parent.pk)
        FolderMembership.objects.create(folder=cls.child_folder, object_id=cls.prefix_child.pk)

        # Dynamic folder backed by a saved filter.
        cls.saved_filter = SavedFilter.objects.create(
            name='All Prefixes', slug='all-prefixes', shared=True, parameters={},
        )
        cls.saved_filter.object_types.set([cls.prefix_ct])
        cls.dynamic_folder = Folder.objects.create(
            name='Dynamic', catalog=cls.catalog, folder_type=Folder.DYNAMIC,
            saved_filter=cls.saved_filter,
        )

        cls.unsupported_folder = Folder.objects.create(
            name='Unsupported Folder', catalog=cls.unsupported_catalog,
            folder_type=Folder.STATIC,
        )

    # ── Prefix tree ──────────────────────────────────────────────────────────

    def test_prefix_tree_view(self):
        url = reverse('plugins:netbox_folderview:prefix_tree')
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_prefix_children_view(self):
        url = reverse('plugins:netbox_folderview:prefix_children', kwargs={'pk': self.prefix_parent.pk})
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_prefix_ips_view(self):
        url = reverse('plugins:netbox_folderview:prefix_ips', kwargs={'pk': self.prefix_parent.pk})
        self.assertEqual(self.client.get(url).status_code, 200)

    # ── Folder objects (HTMX partial) ────────────────────────────────────────

    def test_folder_objects_static_with_nested(self):
        url = reverse('plugins:netbox_folderview:folder_objects', kwargs={'pk': self.folder.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        # show_nested_objects=True → child folder's object is included.
        self.assertIn('10.0.0.0/16', content)
        self.assertIn('10.0.1.0/24', content)

    def test_folder_objects_static_without_nested(self):
        self.folder.show_nested_objects = False
        self.folder.save()
        url = reverse('plugins:netbox_folderview:folder_objects', kwargs={'pk': self.folder.pk})
        content = self.client.get(url).content.decode()
        self.assertIn('10.0.0.0/16', content)
        self.assertNotIn('10.0.1.0/24', content)

    def test_folder_objects_dynamic(self):
        url = reverse('plugins:netbox_folderview:folder_objects', kwargs={'pk': self.dynamic_folder.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Empty saved-filter parameters → all prefixes returned.
        content = response.content.decode()
        self.assertIn('10.0.0.0/16', content)

    def test_folder_objects_unsupported_type(self):
        url = reverse('plugins:netbox_folderview:folder_objects', kwargs={'pk': self.unsupported_folder.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Unsupported object type', response.content.decode())

    # ── Add objects ──────────────────────────────────────────────────────────

    def test_add_objects_get(self):
        url = reverse('plugins:netbox_folderview:folder_add_objects', kwargs={'pk': self.folder.pk})
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_add_objects_post(self):
        folder = Folder.objects.create(
            name='Target', catalog=self.catalog, folder_type=Folder.STATIC,
        )
        url = reverse('plugins:netbox_folderview:folder_add_objects', kwargs={'pk': folder.pk})
        response = self.client.post(url, data={'pk': [self.prefix_parent.pk, self.prefix_child.pk]})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            FolderMembership.objects.filter(folder=folder).count(), 2
        )

    def test_add_objects_respects_allow_duplicates_false(self):
        folder_a = Folder.objects.create(
            name='A', catalog=self.nodup_catalog, folder_type=Folder.STATIC,
        )
        folder_b = Folder.objects.create(
            name='B', catalog=self.nodup_catalog, folder_type=Folder.STATIC,
        )
        FolderMembership.objects.create(folder=folder_a, object_id=self.prefix_parent.pk)

        url = reverse('plugins:netbox_folderview:folder_add_objects', kwargs={'pk': folder_b.pk})
        self.client.post(url, data={'pk': [self.prefix_parent.pk]})
        # Object already lives in folder_a → skipped, not added to folder_b.
        self.assertFalse(
            FolderMembership.objects.filter(folder=folder_b, object_id=self.prefix_parent.pk).exists()
        )

    # ── Remove objects ───────────────────────────────────────────────────────

    def test_remove_objects_post(self):
        folder = Folder.objects.create(
            name='Removable', catalog=self.catalog, folder_type=Folder.STATIC,
        )
        FolderMembership.objects.create(folder=folder, object_id=self.prefix_parent.pk)
        url = reverse('plugins:netbox_folderview:folder_remove_objects', kwargs={'pk': folder.pk})
        response = self.client.post(url, data={'pk': [self.prefix_parent.pk]})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(FolderMembership.objects.filter(folder=folder).exists())

    # ── Move objects ─────────────────────────────────────────────────────────

    def test_move_objects_step1_renders_picker(self):
        url = reverse('plugins:netbox_folderview:folder_move_objects', kwargs={'pk': self.folder.pk})
        response = self.client.post(url, data={'pk': [self.prefix_parent.pk]})
        self.assertEqual(response.status_code, 200)

    def test_move_objects_step2_moves(self):
        source = Folder.objects.create(
            name='Source', catalog=self.catalog, folder_type=Folder.STATIC,
        )
        destination = Folder.objects.create(
            name='Destination', catalog=self.catalog, folder_type=Folder.STATIC,
        )
        FolderMembership.objects.create(folder=source, object_id=self.prefix_parent.pk)

        url = reverse('plugins:netbox_folderview:folder_move_objects', kwargs={'pk': source.pk})
        response = self.client.post(url, data={
            'pk': [self.prefix_parent.pk],
            'destination_folder': destination.pk,
        })
        self.assertEqual(response.status_code, 302)
        self.assertFalse(FolderMembership.objects.filter(folder=source).exists())
        self.assertTrue(
            FolderMembership.objects.filter(folder=destination, object_id=self.prefix_parent.pk).exists()
        )

    # ── Duplicates ───────────────────────────────────────────────────────────

    def test_catalog_duplicates_view(self):
        folder_a = Folder.objects.create(
            name='Dup A', catalog=self.nodup_catalog, folder_type=Folder.STATIC,
        )
        folder_b = Folder.objects.create(
            name='Dup B', catalog=self.nodup_catalog, folder_type=Folder.STATIC,
        )
        FolderMembership.objects.create(folder=folder_a, object_id=self.prefix_parent.pk)
        FolderMembership.objects.create(folder=folder_b, object_id=self.prefix_parent.pk)

        url = reverse('plugins:netbox_folderview:catalog_duplicates', kwargs={'pk': self.nodup_catalog.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['duplicate_count'], 1)

    # ── FolderEditView.alter_object prepopulation ────────────────────────────

    def test_folder_add_prepopulates_from_query_params(self):
        # The add view is an ObjectEditView, which requires the 'add' permission
        # (EXEMPT_VIEW_PERMISSIONS only covers the 'view' action).
        self.add_permissions('netbox_folderview.add_folder')
        url = reverse('plugins:netbox_folderview:folder_add')
        response = self.client.get(f'{url}?catalog={self.catalog.pk}&parent={self.folder.pk}')
        self.assertEqual(response.status_code, 200)
        form_instance = response.context['form'].instance
        self.assertEqual(form_instance.catalog_id, self.catalog.pk)
        self.assertEqual(form_instance.parent_id, self.folder.pk)
