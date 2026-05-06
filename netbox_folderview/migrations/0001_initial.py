import django.core.validators
import django.db.models.deletion
import netbox.models.deletion
import taggit.managers
import utilities.json
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('extras', '0134_owner'),
    ]

    operations = [
        migrations.CreateModel(
            name='Catalog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                ('custom_field_data', models.JSONField(
                    blank=True,
                    default=dict,
                    encoder=utilities.json.CustomFieldJSONEncoder,
                )),
                ('name', models.CharField(
                    max_length=100,
                    validators=[django.core.validators.RegexValidator(
                        regex=r'^[\w\s\-]+$',
                        message='Only letters, numbers, spaces, dashes, and underscores are allowed.',
                    )],
                )),
                ('description', models.CharField(blank=True, max_length=200)),
                ('allow_duplicates', models.BooleanField(default=True)),
                ('default_show_nested_objects', models.BooleanField(default=True)),
                ('object_type', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='catalogs',
                    to='contenttypes.contenttype',
                )),
                ('tags', taggit.managers.TaggableManager(through='extras.TaggedItem', to='extras.Tag')),
            ],
            options={
                'verbose_name': 'catalog',
                'verbose_name_plural': 'catalogs',
                'ordering': ('name',),
            },
            bases=(netbox.models.deletion.DeleteMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Folder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                ('custom_field_data', models.JSONField(
                    blank=True,
                    default=dict,
                    encoder=utilities.json.CustomFieldJSONEncoder,
                )),
                ('name', models.CharField(
                    max_length=100,
                    validators=[django.core.validators.RegexValidator(
                        regex=r'^[\w\s\-]+$',
                        message='Only letters, numbers, spaces, dashes, and underscores are allowed.',
                    )],
                )),
                ('folder_type', models.CharField(
                    choices=[('static', 'Static'), ('dynamic', 'Dynamic')],
                    default='static',
                    max_length=10,
                )),
                ('show_nested_objects', models.BooleanField(default=True)),
                ('catalog', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='folders',
                    to='netbox_folderview.catalog',
                )),
                ('parent', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='children',
                    to='netbox_folderview.folder',
                )),
                ('saved_filter', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='catalog_folders',
                    to='extras.savedfilter',
                )),
                ('tags', taggit.managers.TaggableManager(through='extras.TaggedItem', to='extras.Tag')),
            ],
            options={
                'verbose_name': 'folder',
                'verbose_name_plural': 'folders',
                'ordering': ('catalog', 'name'),
            },
            bases=(netbox.models.deletion.DeleteMixin, models.Model),
        ),
        migrations.CreateModel(
            name='FolderMembership',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('object_id', models.PositiveIntegerField()),
                ('folder', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='memberships',
                    to='netbox_folderview.folder',
                )),
            ],
            options={
                'verbose_name': 'folder membership',
                'verbose_name_plural': 'folder memberships',
            },
        ),
        migrations.AddConstraint(
            model_name='foldermembership',
            constraint=models.UniqueConstraint(
                fields=('folder', 'object_id'),
                name='netbox_folderview_foldermembership_unique',
            ),
        ),
    ]
