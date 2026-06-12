from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from netbox.models import NetBoxModel

__all__ = ('Catalog', 'Folder', 'FolderMembership')

_NAME_VALIDATOR = RegexValidator(
    regex=r'^[\w\s\-]+$',
    message=_('Only letters, numbers, spaces, dashes, and underscores are allowed.'),
)


class Catalog(NetBoxModel):
    name = models.CharField(
        max_length=100,
        validators=[_NAME_VALIDATOR],
        verbose_name=_('name'),
    )
    object_type = models.ForeignKey(
        to='contenttypes.ContentType',
        on_delete=models.PROTECT,
        related_name='catalogs',
        verbose_name=_('object type'),
    )
    description = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('description'),
    )
    allow_duplicates = models.BooleanField(
        default=True,
        verbose_name=_('allow duplicates'),
        help_text=_('When disabled, an object may only appear in one static folder within this catalog.'),
    )
    default_show_nested_objects = models.BooleanField(
        default=True,
        verbose_name=_('default: show nested objects'),
        help_text=_('Default value for "show nested objects" on new folders created in this catalog.'),
    )

    class Meta:
        ordering = ('name',)
        verbose_name = _('catalog')
        verbose_name_plural = _('catalogs')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('plugins:netbox_folderview:catalog', args=[self.pk])

    def clean(self):
        super().clean()
        if self.object_type_id:
            from .catalog_config import get_config_for_type
            ct = self.object_type
            if get_config_for_type(f'{ct.app_label}.{ct.model}') is None:
                raise ValidationError({
                    'object_type': _('This object type is not supported by Catalogs.')
                })

    @property
    def object_type_display(self):
        model_class = self.object_type.model_class()
        if model_class:
            return model_class._meta.verbose_name_plural.title()
        return str(self.object_type)


class Folder(NetBoxModel):
    STATIC = 'static'
    DYNAMIC = 'dynamic'
    TYPE_CHOICES = [
        (STATIC, _('Static')),
        (DYNAMIC, _('Dynamic')),
    ]

    name = models.CharField(
        max_length=100,
        validators=[_NAME_VALIDATOR],
        verbose_name=_('name'),
    )
    catalog = models.ForeignKey(
        to='netbox_folderview.Catalog',
        on_delete=models.CASCADE,
        related_name='folders',
        verbose_name=_('catalog'),
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='children',
        null=True,
        blank=True,
        verbose_name=_('parent folder'),
    )
    folder_type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        default=STATIC,
        verbose_name=_('folder type'),
    )
    show_nested_objects = models.BooleanField(
        default=True,
        verbose_name=_('show nested objects'),
        help_text=_('When enabled, objects from all descendant folders are shown recursively.'),
    )
    saved_filter = models.ForeignKey(
        to='extras.SavedFilter',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='catalog_folders',
        verbose_name=_('saved filter'),
    )

    class Meta:
        ordering = ('catalog', 'name')
        verbose_name = _('folder')
        verbose_name_plural = _('folders')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('plugins:netbox_folderview:folder', args=[self.pk])

    def clean(self):
        super().clean()
        if self.parent_id:
            if self.parent.catalog_id != self.catalog_id:
                raise ValidationError({'parent': _('Parent folder must belong to the same catalog.')})
            if self.parent.folder_type == Folder.DYNAMIC and self.folder_type == Folder.STATIC:
                raise ValidationError({'parent': _('Static folders cannot be nested inside dynamic folders.')})
        if self.folder_type == Folder.DYNAMIC:
            if not self.saved_filter_id:
                raise ValidationError({'saved_filter': _('Dynamic folders require a saved filter.')})
            # Validate SavedFilter covers the catalog's object type
            if self.saved_filter_id and self.catalog_id:
                if not self.saved_filter.object_types.filter(pk=self.catalog.object_type_id).exists():
                    raise ValidationError({
                        'saved_filter': _('The selected saved filter does not apply to this catalog\'s object type.')
                    })
        elif self.saved_filter_id:
            raise ValidationError({'saved_filter': _('Static folders cannot have a saved filter.')})


class FolderMembership(models.Model):
    folder = models.ForeignKey(
        Folder,
        on_delete=models.CASCADE,
        related_name='memberships',
        verbose_name=_('folder'),
    )
    object_id = models.PositiveIntegerField(
        verbose_name=_('object ID'),
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('folder', 'object_id'),
                name='netbox_folderview_foldermembership_unique',
            ),
        ]
        verbose_name = _('folder membership')
        verbose_name_plural = _('folder memberships')

    def __str__(self):
        return f'{self.folder} – {self.object_id}'
