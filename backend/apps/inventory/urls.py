from django.urls import path
from inventory.views import (
    MagicBagListCreateView,
    AvailableMagicBagsView,
    AdminPendingBagsListView,
    AdminApproveRejectBagView,
)

urlpatterns = [
    path('bags/', MagicBagListCreateView.as_view(), name='magic_bags'),
    path('available-bags/', AvailableMagicBagsView.as_view(), name='available_magic_bags'),
    path('admin/pending/', AdminPendingBagsListView.as_view(), name='admin_pending_bags'),
    path('admin/bags/<int:pk>/action/', AdminApproveRejectBagView.as_view(), name='admin_bag_action'),
]
