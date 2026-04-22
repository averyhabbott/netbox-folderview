from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Exists, OuterRef, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, render
from django.views.generic import View

from ipam.choices import PrefixStatusChoices
from ipam.models import IPAddress, Prefix

from .filtersets import FolderViewPrefixFilterSet
from .forms import FolderViewFilterForm
from .tables import PrefixIPTable, PrefixTreeTable

__all__ = (
    'BaseTreeView',
    'PrefixChildrenView',
    'PrefixIPListView',
    'PrefixTreeView',
)

MAX_TREE_DEPTH = 20


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
    """
    Annotate a queryset with _vrf_key = COALESCE(vrf_id, -1) so that NULL VRFs
    compare equal to each other. -1 is never a valid VRF pk.
    """
    return qs.annotate(_vrf_key=Coalesce('vrf_id', Value(-1)))


def _annotate_has_children(queryset, filtered_qs):
    """
    Annotate each prefix in queryset with has_children_in_set — True if any
    prefix in filtered_qs is numerically contained by it (within the same VRF).
    Avoids N+1 by pushing the existence check into a single SQL subquery.
    Uses COALESCE for NULL-safe VRF comparison (NULL = NULL is FALSE in SQL).
    """
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
        # Root = no ancestor exists in the filtered set (VRF-scoped to avoid cross-VRF matches).
        # Uses COALESCE for NULL-safe VRF comparison (NULL = NULL is FALSE in SQL).
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
        ip_table = PrefixIPTable(Prefix.objects.none())
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
    """
    htmx partial — returns direct child prefix nodes for a given prefix.
    Accepts the same filter params as the main page via query string.
    """

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

        # Mirror get_child_prefixes(): global containers (vrf=None + status=container)
        # span all VRFs; all other prefixes are scoped to their own VRF.
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
    """
    htmx partial — returns the paginated IP address table for a given prefix.
    """

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
