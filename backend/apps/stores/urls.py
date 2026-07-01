from django.urls import path, include
from rest_framework.routers import DefaultRouter
from stores.views import StoreProfileView, MyStoreView, UserAddressViewSet

router = DefaultRouter()
router.register(r'addresses', UserAddressViewSet, basename='useraddress')

urlpatterns = [
    path('profile/', StoreProfileView.as_view(), name='store_profile'),
    path('my-store/', MyStoreView.as_view(), name='my_store'),
    path('', include(router.urls)),
]
