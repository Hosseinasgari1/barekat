from rest_framework import serializers
from orders.models import Order
from inventory.models import MagicBag
from stores.models import Store
from users.serializers import UserSerializer


class StoreDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ('name', 'description', 'address', 'latitude', 'longitude')


class MagicBagDetailSerializer(serializers.ModelSerializer):
    store = StoreDetailSerializer(read_only=True)

    class Meta:
        model = MagicBag
        fields = ('id', 'store', 'original_price', 'platform_price', 'pickup_start_time', 'pickup_end_time')


class OrderSerializer(serializers.ModelSerializer):
    magic_bag_details = MagicBagDetailSerializer(source='magic_bag', read_only=True)
    customer_details = UserSerializer(source='customer', read_only=True)

    class Meta:
        model = Order
        fields = (
            'id',
            'customer',
            'customer_details',
            'magic_bag',
            'magic_bag_details',
            'quantity',
            'total_price',
            'status',
            'pickup_code',
            'created_at',
            'updated_at'
        )
        read_only_fields = ('id', 'customer', 'total_price', 'status', 'pickup_code', 'created_at', 'updated_at')

