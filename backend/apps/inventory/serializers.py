from rest_framework import serializers
from inventory.models import MagicBag, MasterProduct
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
            'image',
            'catalog_image_url',
            'expiry_image',
            'approval_status',
            'original_price',
            'platform_price',
            'quantity',
            'pickup_start_time',
            'pickup_end_time',
            'is_active',
            'created_at'
        )
        read_only_fields = ('id', 'store', 'seller', 'approval_status', 'created_at')


class AvailableMagicBagSerializer(serializers.ModelSerializer):
    store = StoreBriefSerializer(read_only=True)
    seller_details = UserSerializer(source='seller', read_only=True)
    distance = serializers.FloatField(read_only=True, required=False)
    seller_rating = serializers.FloatField(read_only=True, required=False, allow_null=True)
    seller_rating_count = serializers.IntegerField(read_only=True, required=False)

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
            'image',
            'catalog_image_url',
            'expiry_image',
            'approval_status',
            'original_price',
            'platform_price',
            'quantity',
            'pickup_start_time',
            'pickup_end_time',
            'is_active',
            'distance',
            'seller_rating',
            'seller_rating_count',
            'created_at',
            'updated_at',
        )


class MasterProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = MasterProduct
        fields = (
            'id', 'title', 'brand', 'category', 'barcode',
            'image_url', 'unit', 'description', 'source'
        )
