from django.urls import path
from users.views import (
    RegisterView, UserProfileView, SendOTPView, VerifyOTPView,
    AdminLoginView, AdminManagementView, AdminDetailView, AdminPermissionsView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('send-otp/', SendOTPView.as_view(), name='send_otp'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify_otp'),
    # Admin auth & management
    path('admin/login/', AdminLoginView.as_view(), name='admin_login'),
    path('admin/permissions/', AdminPermissionsView.as_view(), name='admin_permissions'),
    path('admin/admins/', AdminManagementView.as_view(), name='admin_management'),
    path('admin/admins/<str:pk>/', AdminDetailView.as_view(), name='admin_detail'),
]
