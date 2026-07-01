from rest_framework import serializers
from stores.models import Store, UserAddress


class UserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAddress
        fields = ('id', 'user', 'name', 'latitude', 'longitude', 'is_active', 'created_at')
        read_only_fields = ('id', 'user', 'is_active', 'created_at')


class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ('owner', 'name', 'description', 'address', 'latitude', 'longitude', 'status', 'created_at')
        read_only_fields = ('owner', 'status', 'created_at')

