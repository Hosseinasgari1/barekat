import re
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from users.serializers import (
    UserSerializer, RegisterSerializer, AdminSerializer, AdminCreateSerializer,
    ADMIN_PERMISSION_CHOICES,
)
from users.otp import generate_otp, store_otp, verify_otp, send_mock_sms

User = get_user_model()


class IsAdmin(permissions.BasePermission):
    """Allows access only to authenticated admin accounts."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == User.Roles.ADMIN)


class IsSuperAdmin(permissions.BasePermission):
    """Allows access only to the main (super) admin."""
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated
            and request.user.role == User.Roles.ADMIN
            and request.user.is_super_admin
        )



def normalize_phone_number(phone):
    """Normalizes Iranian phone numbers to start with '09'."""
    phone = str(phone).strip()
    if phone.startswith('+98'):
        phone = '0' + phone[3:]
    elif phone.startswith('0098'):
        phone = '0' + phone[4:]
    elif phone.startswith('9') and len(phone) == 10:
        phone = '0' + phone
    return phone


class SendOTPView(APIView):
    """View to validate phone number and send OTP."""
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        phone_number = request.data.get('phone_number')
        if not phone_number:
            return Response({'error': 'شماره تلفن همراه الزامی است.'}, status=status.HTTP_400_BAD_REQUEST)

        # Iranian phone number validation (starts with 09, +989, or 9 followed by 9 digits)
        pattern = r'^(\+98|0)?9\d{9}$'
        if not re.match(pattern, str(phone_number)):
            return Response({'error': 'فرمت شماره تلفن همراه نامعتبر است.'}, status=status.HTTP_400_BAD_REQUEST)

        normalized_phone = normalize_phone_number(phone_number)
        otp = generate_otp()
        
        # Save to Redis and trigger mock SMS
        store_otp(normalized_phone, otp)
        send_mock_sms(normalized_phone, otp)

        return Response({
            'detail': 'کد تایید با موفقیت ارسال شد.',
            'otp': otp
        }, status=status.HTTP_200_OK)


class VerifyOTPView(APIView):
    """View to verify OTP and return JWT tokens.
    Creates user with default CUSTOMER or specified role if not exists.
    """
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        phone_number = request.data.get('phone_number')
        otp = request.data.get('otp')
        role = request.data.get('role', User.Roles.CUSTOMER)

        if not phone_number or not otp:
            return Response({'error': 'شماره تلفن همراه و کد تایید الزامی هستند.'}, status=status.HTTP_400_BAD_REQUEST)

        normalized_phone = normalize_phone_number(phone_number)

        # Validate OTP
        if not verify_otp(normalized_phone, otp):
            return Response({'error': 'کد تایید نامعتبر یا منقضی شده است.'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate role
        if role not in User.Roles.values:
            role = User.Roles.CUSTOMER

        # Auto-create user if not exist with default/specified role
        user, created = User.objects.get_or_create(
            phone_number=normalized_phone,
            defaults={'role': role, 'is_active': True}
        )

        # Generate simplejwt tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'phone_number': user.phone_number,
                'role': user.role,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email
            }
        }, status=status.HTTP_200_OK)


class RegisterView(generics.CreateAPIView):
    """View to handle user registration."""
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer


class UserProfileView(generics.RetrieveUpdateAPIView):
    """View to retrieve or update the current authenticated user's profile."""
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class AdminLoginView(APIView):
    """Separate login for admins using username + password (no OTP)."""
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        if not username or not password:
            return Response({'error': 'نام کاربری و رمز عبور الزامی هستند.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(admin_username=username.strip(), role=User.Roles.ADMIN)
        except User.DoesNotExist:
            return Response({'error': 'نام کاربری یا رمز عبور نادرست است.'}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active or not user.check_password(password):
            return Response({'error': 'نام کاربری یا رمز عبور نادرست است.'}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'phone_number': user.phone_number,
                'role': user.role,
                'admin_username': user.admin_username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_super_admin': user.is_super_admin,
                'admin_permissions': user.admin_permissions,
            }
        }, status=status.HTTP_200_OK)


class AdminPermissionsView(APIView):
    """Returns the list of assignable admin permissions."""
    permission_classes = (permissions.IsAuthenticated, IsSuperAdmin)

    def get(self, request):
        return Response({'permissions': ADMIN_PERMISSION_CHOICES}, status=status.HTTP_200_OK)


class AdminManagementView(APIView):
    """Super admin lists all sub-admins or creates a new one."""
    permission_classes = (permissions.IsAuthenticated, IsSuperAdmin)

    def get(self, request):
        admins = User.objects.filter(role=User.Roles.ADMIN).order_by('-created_at')
        serializer = AdminSerializer(admins, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = AdminCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        admin = serializer.save()
        return Response(AdminSerializer(admin).data, status=status.HTTP_201_CREATED)


class AdminDetailView(APIView):
    """Super admin updates permissions or deletes a sub-admin."""
    permission_classes = (permissions.IsAuthenticated, IsSuperAdmin)

    def _get_admin(self, pk):
        return get_object_or_404(User, phone_number=pk, role=User.Roles.ADMIN)

    def patch(self, request, pk):
        admin = self._get_admin(pk)
        if admin.is_super_admin:
            return Response({'error': 'نمی‌توانید مدیر اصلی را تغییر دهید.'}, status=status.HTTP_400_BAD_REQUEST)

        perms = request.data.get('admin_permissions')
        if perms is not None:
            invalid = [p for p in perms if p not in ADMIN_PERMISSION_CHOICES]
            if invalid:
                return Response({'error': f'دسترسی نامعتبر: {invalid}'}, status=status.HTTP_400_BAD_REQUEST)
            admin.admin_permissions = perms

        if 'is_active' in request.data:
            admin.is_active = bool(request.data.get('is_active'))

        password = request.data.get('password')
        if password:
            admin.set_password(password)

        admin.save()
        return Response(AdminSerializer(admin).data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        admin = self._get_admin(pk)
        if admin.is_super_admin:
            return Response({'error': 'نمی‌توانید مدیر اصلی را حذف کنید.'}, status=status.HTTP_400_BAD_REQUEST)
        admin.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

