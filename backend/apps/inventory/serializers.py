from rest_framework import serializers
from inventory.models import MagicBag
from stores.models import Store
from users.serializers import UserSerializer


class StoreBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ('id', 'name', 'description', 'address', 'latitude', 'longitude')


class MagicBagSerializer(serializers.ModelSerializer):
    class Meta:
        model = MagicBag
        fields = (
            'id',
            'store',
            'seller',
            'name',
            'description',
            'category',
            'latitude',
            'longitude',
            'original_price',
            'platform_price',
            'quantity',
            'pickup_start_time',
            'pickup_end_time',
            'is_active',
            'created_at'
        )
        read_only_fields = ('id', 'store', 'seller', 'created_at')


class AvailableMagicBagSerializer(serializers.ModelSerializer):
    store = StoreBriefSerializer(read_only=True)
    seller_details = UserSerializer(source='seller', read_only=True)
    distance = serializers.FloatField(read_only=True, required=False)

    class Meta:
        model = MagicBag
        fields = (
            'id',
            'store',
            'seller',
            'seller_details',
            'name',
            'description',
            'category',
            'latitude',
            'longitude',
            'original_price',
            'platform_price',
            'quantity',
            'pickup_start_time',
            'pickup_end_time',
            'distance',
            'created_at'
        )

