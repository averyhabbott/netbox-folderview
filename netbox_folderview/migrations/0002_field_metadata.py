import django.core.validators
import django.db.models.deletion
from django.db import migrations, models
from django.utils.translation import gettext_lazy as _


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('extras', '0134_owner'),
        ('netbox_folderview', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='catalog',
            name='name',
            field=models.CharField(
                max_length=100,
                validators=[django.core.validators.RegexValidator(
                    regex=r'^[\w\s\-]+$',
                    message=_('Only letters, numbers, spaces, dashes, and underscores are allowed.'),
                )],
                verbose_name=_('name'),
            ),
        ),
        migrations.AlterField(
            model_name='catalog',
            name='object_type',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='catalogs',
                to='contenttypes.contenttype',
                verbose_name=_('object type'),
            ),
        ),
        migrations.AlterField(
            model_name='catalog',
            name='description',
            field=models.CharField(
                blank=True,
                max_length=200,
                verbose_name=_('description'),
            ),
        ),
        migrations.AlterField(
            model_name='catalog',
            name='allow_duplicates',
            field=models.BooleanField(
                default=True,
                help_text=_('When disabled, an object may only appear in one static folder within this catalog.'),
                verbose_name=_('allow duplicates'),
            ),
        ),
        migrations.AlterField(
            model_name='catalog',
            name='default_show_nested_objects',
            field=models.BooleanField(
                default=True,
                help_text=_('Default value for "show nested objects" on new folders created in this catalog.'),
                verbose_name=_('default: show nested objects'),
            ),
        ),
        migrations.AlterField(
            model_name='folder',
            name='name',
            field=models.CharField(
                max_length=100,
                validators=[django.core.validators.RegexValidator(
                    regex=r'^[\w\s\-]+$',
                    message=_('Only letters, numbers, spaces, dashes, and underscores are allowed.'),
                )],
                verbose_name=_('name'),
            ),
        ),
        migrations.AlterField(
            model_name='folder',
            name='catalog',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='folders',
                to='netbox_folderview.catalog',
                verbose_name=_('catalog'),
            ),
        ),
        migrations.AlterField(
            model_name='folder',
            name='parent',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='children',
                to='netbox_folderview.folder',
                verbose_name=_('parent folder'),
            ),
        ),
        migrations.AlterField(
            model_name='folder',
            name='folder_type',
            field=models.CharField(
                choices=[('static', _('Static')), ('dynamic', _('Dynamic'))],
                default='static',
                max_length=10,
                verbose_name=_('folder type'),
            ),
        ),
        migrations.AlterField(
            model_name='folder',
            name='show_nested_objects',
            field=models.BooleanField(
                default=True,
                help_text=_('When enabled, objects from all descendant folders are shown recursively.'),
                verbose_name=_('show nested objects'),
            ),
        ),
        migrations.AlterField(
            model_name='folder',
            name='saved_filter',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='catalog_folders',
                to='extras.savedfilter',
                verbose_name=_('saved filter'),
            ),
        ),
        migrations.AlterField(
            model_name='foldermembership',
            name='folder',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='memberships',
                to='netbox_folderview.folder',
                verbose_name=_('folder'),
            ),
        ),
        migrations.AlterField(
            model_name='foldermembership',
            name='object_id',
            field=models.PositiveIntegerField(
                verbose_name=_('object ID'),
            ),
        ),
    ]
