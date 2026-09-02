from django.urls import path
from inventory.views import (
    MagicBagListCreateView,
    AvailableMagicBagsView,
    AdminPendingBagsListView,
    AdminBagsListView,
    AdminApproveRejectBagView,
    MasterCatalogSearchView,
    CatalogSourcesView,
    CatalogCategoriesView,
    CatalogProductsView,
)

urlpatterns = [
    path('bags/', MagicBagListCreateView.as_view(), name='magic_bags'),
    path('available-bags/', AvailableMagicBagsView.as_view(), name='available_magic_bags'),
    path('catalog/search/', MasterCatalogSearchView.as_view(), name='catalog_search'),
    path('catalog/sources/', CatalogSourcesView.as_view(), name='catalog_sources'),
    path('catalog/categories/', CatalogCategoriesView.as_view(), name='catalog_categories'),
    path('catalog/products/', CatalogProductsView.as_view(), name='catalog_products'),
    path('admin/pending/', AdminPendingBagsListView.as_view(), name='admin_pending_bags'),
    path('admin/bags/', AdminBagsListView.as_view(), name='admin_bags'),
    path('admin/bags/<int:pk>/action/', AdminApproveRejectBagView.as_view(), name='admin_bag_action'),
]
