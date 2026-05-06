from django import forms
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _

from extras.models import SavedFilter
from ipam.forms import PrefixFilterForm
from netbox.forms import NetBoxModelFilterSetForm, NetBoxModelForm
from utilities.forms.fields import ContentTypeChoiceField
from utilities.forms.rendering import FieldSet

from .catalog_config import get_catalog_type_queryset
from .models import Catalog, Folder

__all__ = (
    'CatalogFilterForm',
    'CatalogForm',
    'FolderForm',
    'FolderViewFilterForm',
)


class FolderViewFilterForm(PrefixFilterForm):
    pass


class CatalogForm(NetBoxModelForm):
    object_type = ContentTypeChoiceField(
        queryset=ContentType.objects.none(),  # populated in __init__
        label=_('Object Type'),
        help_text=_('The type of objects that can be stored in this catalog.'),
    )

    fieldsets = (
        FieldSet(
            'name', 'object_type', 'description', 'allow_duplicates',
            'default_show_nested_objects', 'tags',
            name=_('Catalog'),
        ),
    )

    class Meta:
        model = Catalog
        fields = ('name', 'object_type', 'description', 'allow_duplicates', 'default_show_nested_objects', 'tags')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['object_type'].queryset = get_catalog_type_queryset()


class CatalogFilterForm(NetBoxModelFilterSetForm):
    model = Catalog

    name = forms.CharField(required=False)
    allow_duplicates = forms.NullBooleanField(
        required=False,
        widget=forms.Select(choices=(
            ('', '---------'),
            (True, _('Yes')),
            (False, _('No')),
        )),
        label=_('Allow Duplicates'),
    )


class FolderForm(NetBoxModelForm):
    catalog = forms.ModelChoiceField(
        queryset=Catalog.objects.all(),
        widget=forms.HiddenInput(),
    )
    parent = forms.ModelChoiceField(
        queryset=Folder.objects.none(),
        required=False,
        label=_('Parent Folder'),
    )
    saved_filter = forms.ModelChoiceField(
        queryset=SavedFilter.objects.filter(shared=True),
        required=False,
        label=_('Saved Filter'),
        help_text=_('Only shared (global) saved filters for this catalog\'s object type are shown. Required for dynamic folders.'),
    )

    fieldsets = (
        FieldSet('name', 'parent', 'folder_type', 'show_nested_objects', 'saved_filter', 'tags', name=_('Folder')),
    )

    class Meta:
        model = Folder
        fields = ('name', 'catalog', 'parent', 'folder_type', 'show_nested_objects', 'saved_filter', 'tags')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Determine the catalog from the instance or POST data
        catalog = None
        if self.instance and self.instance.catalog_id:
            try:
                catalog = Catalog.objects.get(pk=self.instance.catalog_id)
            except Catalog.DoesNotExist:
                pass
        if catalog is None and self.data.get('catalog'):
            try:
                catalog = Catalog.objects.get(pk=self.data['catalog'])
            except (Catalog.DoesNotExist, ValueError):
                pass

        if catalog:
            self.fields['parent'].queryset = Folder.objects.filter(catalog=catalog)
            self.fields['saved_filter'].queryset = SavedFilter.objects.filter(
                shared=True,
                object_types=catalog.object_type,
            )
            if not self.instance.pk:
                self.initial['show_nested_objects'] = catalog.default_show_nested_objects
