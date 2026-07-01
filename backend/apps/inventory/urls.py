from django.urls import path
from inventory.views import MagicBagListCreateView, AvailableMagicBagsView

urlpatterns = [
    path('bags/', MagicBagListCreateView.as_view(), name='magic_bags'),
    path('available-bags/', AvailableMagicBagsView.as_view(), name='available_magic_bags'),
]
