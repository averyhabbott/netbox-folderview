from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Exists, OuterRef, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import View

from ipam.choices import PrefixStatusChoices
from ipam.models import IPAddress, Prefix
from netbox.views import generic
from utilities.tables import get_table_configs

from .catalog_config import get_config_for_type
from .filtersets import CatalogFilterSet, FolderViewPrefixFilterSet
from .forms import CatalogFilterForm, CatalogForm, FolderForm, FolderViewFilterForm
from .models import Catalog, Folder, FolderMembership
from .tables import CatalogTable, PrefixIPTable, PrefixTreeTable

__all__ = (
    'BaseTreeView',
    'CatalogDeleteView',
    'CatalogDetailView',
    'CatalogDuplicatesView',
    'FolderAddObjectsView',
    'FolderMoveObjectsView',
    'FolderRemoveObjectsView',
    'CatalogEditView',
    'CatalogListView',
    'FolderDeleteView',
    'FolderDetailView',
    'FolderEditView',
    'FolderObjectsView',
    'PrefixChildrenView',
    'PrefixIPListView',
    'PrefixTreeView',
)

MAX_TREE_DEPTH = 20


# ── Prefix tree views (existing) ──────────────────────────────────────────────

class BaseTreeView(LoginRequiredMixin, View):
    filterset_class = None
    filter_form_class = None
    tree_table_class = None

    def get_filtered_queryset(self, request):
        raise NotImplementedError

    def get_root_nodes(self, filtered_qs):
        raise NotImplementedError


def _strip_depth(query_dict):
    """Return a mutable copy of a QueryDict with 'depth' removed."""
    params = query_dict.copy()
    params.pop('depth', None)
    return params


def _vrf_safe(qs):
    return qs.annotate(_vrf_key=Coalesce('vrf_id', Value(-1)))


def _annotate_has_children(queryset, filtered_qs):
    child_exists = _vrf_safe(filtered_qs).filter(
        prefix__net_contained=OuterRef('prefix'),
        _vrf_key=Coalesce(OuterRef('vrf_id'), Value(-1)),
    )
    return queryset.annotate(has_children_in_set=Exists(child_exists))


class PrefixTreeView(BaseTreeView):
    filterset_class = FolderViewPrefixFilterSet
    filter_form_class = FolderViewFilterForm
    tree_table_class = PrefixTreeTable
    template_name = 'netbox_folderview/prefix_tree.html'

    def get_filtered_queryset(self, request):
        qs = Prefix.objects.restrict(request.user, 'view').prefetch_related('vrf', 'role', 'tenant')
        return self.filterset_class(request.GET, qs, request=request).qs

    def get_root_nodes(self, filtered_qs):
        ancestor_exists = _vrf_safe(filtered_qs).filter(
            prefix__net_contains=OuterRef('prefix'),
            _vrf_key=Coalesce(OuterRef('vrf_id'), Value(-1)),
        ).values('pk')[:1]
        roots = filtered_qs.annotate(
            has_ancestor_in_set=Exists(ancestor_exists)
        ).filter(has_ancestor_in_set=False).order_by('vrf', 'prefix')
        return _annotate_has_children(roots, filtered_qs)

    def get(self, request):
        filtered_qs = self.get_filtered_queryset(request)
        root_nodes = self.get_root_nodes(filtered_qs)
        root_rows = [
            {'prefix': p, 'has_children': p.has_children_in_set}
            for p in root_nodes
        ]

        filter_form = self.filter_form_class(request.GET)
        tree_table = PrefixTreeTable(Prefix.objects.none())
        tree_table.configure(request)
        ip_table = PrefixIPTable(IPAddress.objects.none())
        ip_table.configure(request)
        tree_columns = [col[0] for col in tree_table.selected_columns]

        return render(request, self.template_name, {
            'filter_form': filter_form,
            'root_rows': root_rows,
            'filter_params': _strip_depth(request.GET).urlencode(),
            'tree_table': tree_table,
            'tree_columns': tree_columns,
            'ip_table': ip_table,
            'model': Prefix,
        })


class PrefixChildrenView(LoginRequiredMixin, View):
    def get(self, request, pk):
        parent = get_object_or_404(
            Prefix.objects.restrict(request.user, 'view'), pk=pk
        )

        try:
            depth = max(0, min(int(request.GET.get('depth', 0)), MAX_TREE_DEPTH)) + 1
        except (ValueError, TypeError):
            depth = 1

        base_qs = Prefix.objects.restrict(request.user, 'view').prefetch_related('vrf', 'role', 'tenant')
        filtered_qs = FolderViewPrefixFilterSet(_strip_depth(request.GET), base_qs, request=request).qs

        if parent.vrf is None and parent.status == PrefixStatusChoices.STATUS_CONTAINER:
            all_descendants = filtered_qs.filter(prefix__net_contained=str(parent.prefix))
            intermediate_exists = all_descendants.filter(
                prefix__net_contains=OuterRef('prefix'),
            ).exclude(pk=OuterRef('pk')).values('pk')[:1]
        else:
            all_descendants = filtered_qs.filter(
                prefix__net_contained=str(parent.prefix),
                vrf=parent.vrf,
            )
            intermediate_exists = all_descendants.filter(
                prefix__net_contains=OuterRef('prefix'),
                vrf=parent.vrf,
            ).exclude(pk=OuterRef('pk')).values('pk')[:1]

        direct_children = all_descendants.annotate(
            has_intermediate=Exists(intermediate_exists)
        ).filter(has_intermediate=False).order_by('prefix')

        direct_children = _annotate_has_children(direct_children, filtered_qs)
        child_rows = [
            {'prefix': c, 'has_children': c.has_children_in_set}
            for c in direct_children
        ]

        tree_table = PrefixTreeTable(Prefix.objects.none())
        tree_table.configure(request)
        tree_columns = [col[0] for col in tree_table.selected_columns]

        return render(request, 'netbox_folderview/inc/prefix/tree_node.html', {
            'children': child_rows,
            'filter_params': _strip_depth(request.GET).urlencode(),
            'depth': depth,
            'tree_columns': tree_columns,
        })


class PrefixIPListView(LoginRequiredMixin, View):
    def get(self, request, pk):
        prefix = get_object_or_404(
            Prefix.objects.restrict(request.user, 'view'), pk=pk
        )
        ip_qs = (
            prefix.get_child_ips()
            .restrict(request.user, 'view')
            .prefetch_related('vrf', 'tenant')
            .order_by('address')
        )

        table = PrefixIPTable(ip_qs)
        table.configure(request)

        return render(request, 'netbox_folderview/inc/prefix/ip_table.html', {
            'prefix': prefix,
            'table': table,
        })


# ── Catalog views ─────────────────────────────────────────────────────────────

class CatalogListView(generic.ObjectListView):
    queryset = Catalog.objects.annotate(folder_count=Count('folders'))
    filterset = CatalogFilterSet
    filterset_form = CatalogFilterForm
    table = CatalogTable


class CatalogDetailView(generic.ObjectView):
    queryset = Catalog.objects.all()
    template_name = 'netbox_folderview/catalog.html'

    def get_extra_context(self, request, instance):
        all_folders = list(
            Folder.objects.filter(catalog=instance)
            .order_by('name')
            .select_related('saved_filter')
        )

        # Build parent → children map
        children_map = {}
        for folder in all_folders:
            pid = folder.parent_id
            if pid not in children_map:
                children_map[pid] = []
            children_map[pid].append(folder)

        # Flatten into DFS order: [(folder, depth), ...]
        def flatten(parent_id, depth):
            result = []
            for folder in children_map.get(parent_id, []):
                result.append({'folder': folder, 'depth': depth})
                result.extend(flatten(folder.pk, depth + 1))
            return result

        folder_rows = flatten(None, 0)

        return {
            'folder_rows': folder_rows,
        }


class CatalogEditView(generic.ObjectEditView):
    queryset = Catalog.objects.all()
    form = CatalogForm


class CatalogDeleteView(generic.ObjectDeleteView):
    queryset = Catalog.objects.all()


class CatalogDuplicatesView(LoginRequiredMixin, View):
    """
    Shows all objects that appear in more than one static folder within a catalog.
    Only relevant (and only accessible) when allow_duplicates=False is being considered
    or already violated retroactively.
    """

    def get(self, request, pk):
        catalog = get_object_or_404(
            Catalog.objects.restrict(request.user, 'view').select_related('object_type'),
            pk=pk,
        )
        ct = catalog.object_type
        type_key = f'{ct.app_label}.{ct.model}'
        config = get_config_for_type(type_key)

        # Find object_ids that appear in more than one static folder
        from django.db.models import Count as DbCount
        duplicate_ids = (
            FolderMembership.objects.filter(
                folder__catalog=catalog,
                folder__folder_type=Folder.STATIC,
            )
            .values('object_id')
            .annotate(folder_count=DbCount('folder'))
            .filter(folder_count__gt=1)
            .values_list('object_id', flat=True)
        )

        # For each duplicate, gather folder memberships
        memberships = (
            FolderMembership.objects.filter(
                folder__catalog=catalog,
                folder__folder_type=Folder.STATIC,
                object_id__in=list(duplicate_ids),
            )
            .select_related('folder')
            .order_by('object_id', 'folder__name')
        )

        # Group by object_id → list of folders
        groups = {}
        for m in memberships:
            groups.setdefault(m.object_id, []).append(m.folder)

        # Resolve objects if config is available
        rows = []
        if config and groups:
            model = config['model']
            objects_by_pk = {
                obj.pk: obj
                for obj in model.objects.restrict(request.user, 'view').filter(pk__in=groups.keys())
            }
            for obj_pk, folders in sorted(groups.items()):
                rows.append({
                    'obj': objects_by_pk.get(obj_pk),
                    'obj_pk': obj_pk,
                    'folders': folders,
                })

        return render(request, 'netbox_folderview/catalog_duplicates.html', {
            'catalog': catalog,
            'rows': rows,
            'duplicate_count': len(rows),
        })


# ── Folder views ──────────────────────────────────────────────────────────────

class FolderDetailView(generic.ObjectView):
    queryset = Folder.objects.select_related('catalog', 'parent', 'saved_filter')


class FolderEditView(generic.ObjectEditView):
    queryset = Folder.objects.all()
    form = FolderForm

    def alter_object(self, obj, request, url_args, url_kwargs):
        if not obj.pk:
            catalog_pk = request.GET.get('catalog')
            if catalog_pk:
                try:
                    obj.catalog_id = int(catalog_pk)
                except (ValueError, TypeError):
                    pass
            parent_pk = request.GET.get('parent')
            if parent_pk:
                try:
                    obj.parent_id = int(parent_pk)
                except (ValueError, TypeError):
                    pass
        return obj

    def get_return_url(self, request, obj=None):
        if obj and obj.catalog_id:
            return obj.catalog.get_absolute_url()
        return super().get_return_url(request, obj)


class FolderDeleteView(generic.ObjectDeleteView):
    queryset = Folder.objects.all()

    def get_return_url(self, request, obj=None):
        if obj and obj.catalog_id:
            return obj.catalog.get_absolute_url()
        return super().get_return_url(request, obj)


# ── Add Objects to folder ────────────────────────────────────────────────────

class FolderAddObjectsView(generic.ObjectListView):
    """
    Full-page picker for adding objects to a static folder.
    GET: Filtered object list with checkboxes (NCO-style dynamic ObjectListView).
    POST: Creates FolderMembership records for selected PKs.
    """
    template_name = 'netbox_folderview/folder_add_objects.html'
    actions = ()

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.folder = get_object_or_404(
            Folder.objects.select_related('catalog__object_type'),
            pk=kwargs['pk'],
            folder_type=Folder.STATIC,
        )
        catalog = self.folder.catalog
        ct = catalog.object_type
        type_key = f'{ct.app_label}.{ct.model}'
        config = get_config_for_type(type_key)
        if config:
            self.queryset = config['model'].objects.restrict(request.user, 'view')
            self.filterset = config['filterset']
            self.filterset_form = config['filterset_form']
            self.table = config['table']
        else:
            self.queryset = None

    def get(self, request, pk):
        if self.queryset is None:
            messages.error(request, 'Unsupported object type for this catalog.')
            return redirect(self.folder.catalog.get_absolute_url())

        if self.filterset:
            filtered_qs = self.filterset(request.GET, self.queryset, request=request).qs
        else:
            filtered_qs = self.queryset

        table = self.get_table(filtered_qs, request, True)
        filter_form = self.filterset_form(request.GET) if self.filterset_form else None

        return render(request, self.template_name, {
            'model': self.queryset.model,
            'table': table,
            'table_configs': get_table_configs(table, request.user),
            'actions': [],
            'filter_form': filter_form,
            'folder': self.folder,
            **self.get_extra_context(request),
        })

    def post(self, request, pk):
        folder = self.folder
        catalog = folder.catalog
        selected_pks = [int(x) for x in request.POST.getlist('pk') if x.strip().isdigit()]

        added = 0
        skipped = 0
        for obj_pk in selected_pks:
            if not catalog.allow_duplicates:
                already_elsewhere = FolderMembership.objects.filter(
                    folder__catalog=catalog,
                    folder__folder_type=Folder.STATIC,
                    object_id=obj_pk,
                ).exclude(folder=folder).exists()
                if already_elsewhere:
                    skipped += 1
                    continue
            _, created = FolderMembership.objects.get_or_create(
                folder=folder,
                object_id=obj_pk,
            )
            if created:
                added += 1

        if added:
            messages.success(request, f'Added {added} object(s) to "{folder.name}".')
        if skipped:
            messages.warning(
                request,
                f'Skipped {skipped} object(s) that already appear in another folder '
                f'(this catalog does not allow duplicates).'
            )

        return redirect(catalog.get_absolute_url())

    def get_extra_context(self, request):
        return {'folder': self.folder}


# ── HTMX: folder object list (right pane) ────────────────────────────────────

def _get_descendant_folder_ids(folder_pk, children_map):
    """Return all descendant folder PKs via DFS."""
    result = []
    for child in children_map.get(folder_pk, []):
        result.append(child.pk)
        result.extend(_get_descendant_folder_ids(child.pk, children_map))
    return result


class FolderObjectsView(LoginRequiredMixin, View):
    """
    HTMX partial — returns the object table for a given folder.
    Handles both static (FolderMembership) and dynamic (SavedFilter) folders.
    """

    def get(self, request, pk):
        folder = get_object_or_404(
            Folder.objects.restrict(request.user, 'view').select_related(
                'catalog__object_type', 'saved_filter'
            ),
            pk=pk,
        )
        catalog = folder.catalog
        ct = catalog.object_type
        type_key = f'{ct.app_label}.{ct.model}'
        config = get_config_for_type(type_key)

        if config is None:
            return render(request, 'netbox_folderview/inc/catalog/folder_objects.html', {
                'folder': folder,
                'table': None,
                'error': f'Unsupported object type: {type_key}',
            })

        model = config['model']
        table_class = config['table']
        filterset_class = config['filterset']

        base_qs = model.objects.restrict(request.user, 'view')

        if folder.folder_type == Folder.DYNAMIC:
            if not folder.saved_filter_id:
                table = table_class(model.objects.none())
                table.configure(request)
                return render(request, 'netbox_folderview/inc/catalog/folder_objects.html', {
                    'folder': folder,
                    'table': table,
                })
            params = folder.saved_filter.parameters or {}
            qs = filterset_class(params, base_qs, request=request).qs

        else:
            # Static folder — resolve object_ids from memberships
            if folder.show_nested_objects:
                # Build children map for this catalog to get all descendants
                all_siblings = list(Folder.objects.filter(catalog=catalog).only('pk', 'parent_id'))
                children_map = {}
                for f in all_siblings:
                    pid = f.parent_id
                    if pid not in children_map:
                        children_map[pid] = []
                    children_map[pid].append(f)
                descendant_ids = _get_descendant_folder_ids(folder.pk, children_map)
                folder_ids = [folder.pk] + descendant_ids
            else:
                folder_ids = [folder.pk]

            object_ids = list(
                FolderMembership.objects.filter(folder_id__in=folder_ids)
                .values_list('object_id', flat=True)
                .distinct()
            )
            qs = base_qs.filter(pk__in=object_ids)

        table = table_class(qs)
        table.configure(request)
        if folder.folder_type == Folder.STATIC and 'pk' in table.base_columns:
            table.columns.show('pk')

        return render(request, 'netbox_folderview/inc/catalog/folder_objects.html', {
            'folder': folder,
            'table': table,
        })


# ── Remove / Move operations ──────────────────────────────────────────────────

class FolderRemoveObjectsView(LoginRequiredMixin, View):
    def post(self, request, pk):
        folder = get_object_or_404(
            Folder.objects.restrict(request.user, 'view'),
            pk=pk,
            folder_type=Folder.STATIC,
        )
        object_ids = [int(x) for x in request.POST.getlist('pk') if x.strip().isdigit()]
        if object_ids:
            removed, _ = FolderMembership.objects.filter(
                folder=folder, object_id__in=object_ids
            ).delete()
            if removed:
                messages.success(request, f'Removed {removed} object(s) from "{folder.name}".')
        return redirect(folder.catalog.get_absolute_url())


class FolderMoveObjectsView(LoginRequiredMixin, View):
    """
    Two-step move:
      POST (step 1) from folder_objects form — selected_pks provided, no destination yet.
                    Renders the destination picker page.
      POST (step 2) from destination picker — selected_pks + destination provided.
                    Performs the move and redirects to catalog.
    """

    def post(self, request, pk):
        source = get_object_or_404(
            Folder.objects.restrict(request.user, 'view').select_related('catalog'),
            pk=pk,
            folder_type=Folder.STATIC,
        )
        catalog = source.catalog

        selected_pks = [int(x) for x in request.POST.getlist('pk') if x.strip().isdigit()]
        destination_pk = request.POST.get('destination_folder')

        if not selected_pks:
            messages.warning(request, 'No objects selected.')
            return redirect(catalog.get_absolute_url())

        if destination_pk:
            # Step 2: perform the move
            destination = get_object_or_404(
                Folder.objects.restrict(request.user, 'view'),
                pk=destination_pk,
                catalog=catalog,
                folder_type=Folder.STATIC,
            )
            moved = 0
            skipped = 0
            from django.db import transaction
            for obj_pk in selected_pks:
                if not catalog.allow_duplicates:
                    already_elsewhere = FolderMembership.objects.filter(
                        folder__catalog=catalog,
                        folder__folder_type=Folder.STATIC,
                        object_id=obj_pk,
                    ).exclude(folder__in=[source, destination]).exists()
                    if already_elsewhere:
                        skipped += 1
                        continue
                with transaction.atomic():
                    FolderMembership.objects.filter(folder=source, object_id=obj_pk).delete()
                    FolderMembership.objects.get_or_create(folder=destination, object_id=obj_pk)
                moved += 1
            if moved:
                messages.success(request, f'Moved {moved} object(s) to "{destination.name}".')
            if skipped:
                messages.warning(
                    request,
                    f'Skipped {skipped} object(s) (duplicates not allowed in this catalog).'
                )
            return redirect(catalog.get_absolute_url())

        # Step 1: render destination picker
        available_folders = Folder.objects.filter(
            catalog=catalog, folder_type=Folder.STATIC
        ).exclude(pk=source.pk).order_by('name')

        return render(request, 'netbox_folderview/folder_move_objects.html', {
            'source_folder': source,
            'selected_pks': selected_pks,
            'available_folders': available_folders,
        })
