from django.urls import path

from netbox.views import generic

from . import views
from .models import Catalog, Folder

urlpatterns = [
    # Prefix tree (existing)
    path('prefix-tree/', views.PrefixTreeView.as_view(), name='prefix_tree'),
    path('prefix-tree/<int:pk>/children/', views.PrefixChildrenView.as_view(), name='prefix_children'),
    path('prefix-tree/<int:pk>/ips/', views.PrefixIPListView.as_view(), name='prefix_ips'),

    # Catalog CRUD
    path('catalogs/', views.CatalogListView.as_view(), name='catalog_list'),
    path('catalogs/add/', views.CatalogEditView.as_view(), name='catalog_add'),
    path('catalogs/<int:pk>/', views.CatalogDetailView.as_view(), name='catalog'),
    path('catalogs/<int:pk>/edit/', views.CatalogEditView.as_view(), name='catalog_edit'),
    path('catalogs/<int:pk>/delete/', views.CatalogDeleteView.as_view(), name='catalog_delete'),
    path('catalogs/<int:pk>/changelog/', generic.ObjectChangeLogView.as_view(), name='catalog_changelog', kwargs={'model': Catalog}),
    path('catalogs/<int:pk>/duplicates/', views.CatalogDuplicatesView.as_view(), name='catalog_duplicates'),

    # Folder CRUD (catalog passed as ?catalog=<pk> query param on add)
    path('folders/add/', views.FolderEditView.as_view(), name='folder_add'),
    path('folders/<int:pk>/', views.FolderDetailView.as_view(), name='folder'),
    path('folders/<int:pk>/edit/', views.FolderEditView.as_view(), name='folder_edit'),
    path('folders/<int:pk>/delete/', views.FolderDeleteView.as_view(), name='folder_delete'),
    path('folders/<int:pk>/changelog/', generic.ObjectChangeLogView.as_view(), name='folder_changelog', kwargs={'model': Folder}),

    # Add / remove / move objects
    path('folders/<int:pk>/add-objects/', views.FolderAddObjectsView.as_view(), name='folder_add_objects'),
    path('folders/<int:pk>/remove/', views.FolderRemoveObjectsView.as_view(), name='folder_remove_objects'),
    path('folders/<int:pk>/move/', views.FolderMoveObjectsView.as_view(), name='folder_move_objects'),

    # HTMX partials
    path('folders/<int:pk>/objects/', views.FolderObjectsView.as_view(), name='folder_objects'),
]
