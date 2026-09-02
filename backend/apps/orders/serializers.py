from rest_framework import serializers
from orders.models import Order, Review
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
        fields = (
            'id',
            'store',
            'name',
            'description',
            'category',
            'original_price',
            'platform_price',
            'pickup_start_time',
            'pickup_end_time',
        )


class ReviewCustomerSerializer(serializers.Serializer):
    """Public-facing customer info for reviews (masked phone)."""
    display_name = serializers.SerializerMethodField()

    def get_display_name(self, obj):
        name = f"{obj.first_name or ''} {obj.last_name or ''}".strip()
        if name:
            return name
        phone = str(obj.phone_number)
        if len(phone) >= 4:
            return f"کاربر {phone[-4:]}"
        return 'کاربر برکت'


class ReviewSerializer(serializers.ModelSerializer):
    customer = ReviewCustomerSerializer(read_only=True)

    class Meta:
        model = Review
        fields = ('id', 'rating', 'comment', 'customer', 'created_at')
        read_only_fields = ('id', 'customer', 'created_at')

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError('امتیاز باید بین ۱ تا ۵ باشد.')
        return value


class ReviewCreateSerializer(serializers.Serializer):
    rating = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(required=False, allow_blank=True, default='')


class OrderSerializer(serializers.ModelSerializer):
    magic_bag_details = MagicBagDetailSerializer(source='magic_bag', read_only=True)
    customer_details = UserSerializer(source='customer', read_only=True)
    my_review = ReviewSerializer(source='review', read_only=True)

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
            'my_review',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'customer',
            'total_price',
            'status',
            'pickup_code',
            'created_at',
            'updated_at',
        )
