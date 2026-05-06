import importlib

from netbox.registry import registry

# Apps that should never appear as catalog object types
_EXCLUDED_APPS = {'netbox_folderview', 'core', 'users', 'auth', 'contenttypes', 'sessions'}


def get_config_for_type(type_key: str) -> dict | None:
    """
    Dynamically resolve filterset, table, and filter form for a catalog object type.
    Uses NetBox's filterset registry + importlib convention-based lookup.
    Returns None if the type cannot be fully resolved.
    """
    filterset = registry['filtersets'].get(type_key)
    if filterset is None:
        return None

    app_label = type_key.split('.')[0]
    if app_label in _EXCLUDED_APPS:
        return None

    model = filterset.Meta.model
    class_name = model.__name__

    try:
        tables_mod = importlib.import_module(f'{app_label}.tables')
        table = getattr(tables_mod, f'{class_name}Table')
    except (ImportError, AttributeError):
        return None

    try:
        forms_mod = importlib.import_module(f'{app_label}.forms')
        filterset_form = getattr(forms_mod, f'{class_name}FilterForm')
    except (ImportError, AttributeError):
        return None

    return {
        'model': model,
        'table': table,
        'filterset': filterset,
        'filterset_form': filterset_form,
    }


def get_catalog_type_queryset():
    """
    ContentType queryset limited to types that have a registered filterset
    and can be fully resolved to a table + filter form.
    """
    from django.contrib.contenttypes.models import ContentType
    from django.db.models import Q

    q = Q()
    for type_key in registry['filtersets'].keys():
        parts = type_key.split('.')
        if len(parts) != 2:
            continue
        app_label, model_name = parts
        if app_label in _EXCLUDED_APPS:
            continue
        if get_config_for_type(type_key) is not None:
            q |= Q(app_label=app_label, model=model_name)

    return ContentType.objects.filter(q) if q != Q() else ContentType.objects.none()
