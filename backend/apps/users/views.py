import re
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from users.serializers import UserSerializer, RegisterSerializer
from users.otp import generate_otp, store_otp, verify_otp, send_mock_sms

User = get_user_model()


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
