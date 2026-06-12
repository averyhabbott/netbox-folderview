from netbox.api.routers import NetBoxRouter

from .views import CatalogViewSet, FolderViewSet

app_name = 'netbox_folderview'

router = NetBoxRouter()
router.register('catalogs', CatalogViewSet)
router.register('folders', FolderViewSet)

urlpatterns = router.urls
