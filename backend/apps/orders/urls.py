from django.urls import path
from orders.views import (
    OrderCreateView,
    CustomerOrdersView,
    ApproveOrderView,
    RejectOrderView,
    VerifyPickupView,
    VendorOrdersView
)

urlpatterns = [
    path('', OrderCreateView.as_view(), name='order_create'),
    path('my-orders/', CustomerOrdersView.as_view(), name='customer_orders'),
    path('vendor/', VendorOrdersView.as_view(), name='vendor_orders'),
    path('<int:pk>/approve/', ApproveOrderView.as_view(), name='order_approve'),
    path('<int:pk>/reject/', RejectOrderView.as_view(), name='order_reject'),
    path('<int:pk>/verify-pickup/', VerifyPickupView.as_view(), name='order_verify_pickup'),
]

