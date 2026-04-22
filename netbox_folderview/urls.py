from django.urls import path

from . import views

urlpatterns = [
    path('prefix-tree/', views.PrefixTreeView.as_view(), name='prefix_tree'),
    path('prefix-tree/<int:pk>/children/', views.PrefixChildrenView.as_view(), name='prefix_children'),
    path('prefix-tree/<int:pk>/ips/', views.PrefixIPListView.as_view(), name='prefix_ips'),
]
