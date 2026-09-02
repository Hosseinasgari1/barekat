from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

# All permission keys an admin may be granted. Extensible in future.
ADMIN_PERMISSION_CHOICES = ['approve_products']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'phone_number', 'first_name', 'last_name', 'email', 'role', 'date_joined',
            'admin_username', 'is_super_admin', 'admin_permissions',
        )
        read_only_fields = ('phone_number', 'date_joined', 'admin_username', 'is_super_admin', 'admin_permissions')


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ('phone_number', 'password', 'first_name', 'last_name', 'email')

    def create(self, validated_data):
        user = User.objects.create_user(
            phone_number=validated_data['phone_number'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            email=validated_data.get('email', '')
        )
        return user


class AdminSerializer(serializers.ModelSerializer):
    """Read serializer for listing admin accounts (no password)."""
    class Meta:
        model = User
        fields = (
            'phone_number', 'admin_username', 'first_name', 'last_name',
            'is_super_admin', 'admin_permissions', 'is_active', 'created_at',
        )


class AdminCreateSerializer(serializers.Serializer):
    """Create serializer used by a super admin to add a new sub-admin."""
    admin_username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=4, style={'input_type': 'password'})
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default='')
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default='')
    admin_permissions = serializers.ListField(
        child=serializers.ChoiceField(choices=ADMIN_PERMISSION_CHOICES),
        required=False,
        default=list,
    )

    def validate_admin_username(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('نام کاربری الزامی است.')
        if User.objects.filter(admin_username=value).exists():
            raise serializers.ValidationError('این نام کاربری قبلاً استفاده شده است.')
        return value

    def create(self, validated_data):
        username = validated_data['admin_username']
        # phone_number is the PK; for admins we store a non-phone unique identifier.
        phone_identifier = f'admin:{username}'
        user = User(
            phone_number=phone_identifier,
            admin_username=username,
            role=User.Roles.ADMIN,
            is_staff=True,
            is_active=True,
            is_super_admin=False,
            admin_permissions=validated_data.get('admin_permissions', []),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
        )
        user.set_password(validated_data['password'])
        user.save()
        return user
