from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
import random
import string

from orders.models import Order
from orders.serializers import OrderSerializer
from inventory.models import MagicBag
from stores.models import Store


def generate_unique_pickup_code():
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not Order.objects.filter(pickup_code=code).exists():
            return code


class OrderCreateView(APIView):
    """Buyer creates an order. Starts at PENDING_PAYMENT (awaiting seller approval)."""
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        magic_bag_id = request.data.get('magic_bag')
        quantity = int(request.data.get('quantity', 1))

        if not magic_bag_id:
            return Response({'error': 'شناسه کیسه جادویی الزامی است.'}, status=status.HTTP_400_BAD_REQUEST)
        if quantity <= 0:
            return Response({'error': 'تعداد معتبر نیست.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            try:
                magic_bag = MagicBag.objects.select_for_update().get(id=magic_bag_id)
            except MagicBag.DoesNotExist:
                return Response({'error': 'کیسه جادویی یافت نشد.'}, status=status.HTTP_404_NOT_FOUND)

            if not magic_bag.is_active:
                return Response({'error': 'کیسه جادویی فعال نیست.'}, status=status.HTTP_400_BAD_REQUEST)

            if magic_bag.quantity < quantity:
                return Response({'error': 'موجودی کیسه کافی نیست.'}, status=status.HTTP_400_BAD_REQUEST)

            magic_bag.quantity -= quantity
            magic_bag.save()

            total_price = magic_bag.platform_price * quantity
            pickup_code = generate_unique_pickup_code()

            order = Order.objects.create(
                customer=request.user,
                magic_bag=magic_bag,
                quantity=quantity,
                total_price=total_price,
                status=Order.OrderStatus.PENDING_PAYMENT,
                pickup_code=pickup_code
            )

            serializer = OrderSerializer(order)
            return Response(serializer.data, status=status.HTTP_201_CREATED)


class CustomerOrdersView(APIView):
    """List all orders for the authenticated buyer (no pagination)."""
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        orders = Order.objects.filter(customer=request.user).order_by('-created_at')
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ApproveOrderView(APIView):
    """Seller approves a pending order → PENDING_PAYMENT becomes PAID (in progress)."""
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, pk):
        order = get_object_or_404(Order, id=pk)

        # Verify seller permission (either store owner or individual seller)
        if order.magic_bag.store:
            try:
                store = request.user.store
                if order.magic_bag.store != store:
                    return Response({'error': 'این سفارش متعلق به فروشگاه شما نیست.'}, status=status.HTTP_403_FORBIDDEN)
            except (AttributeError, Store.DoesNotExist):
                return Response({'error': 'شما فروشگاهی ندارید.'}, status=status.HTTP_403_FORBIDDEN)
        else:
            if order.magic_bag.seller != request.user:
                return Response({'error': 'این سفارش متعلق به شما نیست.'}, status=status.HTTP_403_FORBIDDEN)

        if order.status != Order.OrderStatus.PENDING_PAYMENT:
            return Response({'error': 'این سفارش قابل تایید نیست.'}, status=status.HTTP_400_BAD_REQUEST)

        order.status = Order.OrderStatus.PAID
        order.save()

        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RejectOrderView(APIView):
    """Seller rejects a pending order → CANCELLED. Inventory is restored."""
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, pk):
        order = get_object_or_404(Order, id=pk)

        # Verify seller permission (either store owner or individual seller)
        if order.magic_bag.store:
            try:
                store = request.user.store
                if order.magic_bag.store != store:
                    return Response({'error': 'این سفارش متعلق به فروشگاه شما نیست.'}, status=status.HTTP_403_FORBIDDEN)
            except (AttributeError, Store.DoesNotExist):
                return Response({'error': 'شما فروشگاهی ندارید.'}, status=status.HTTP_403_FORBIDDEN)
        else:
            if order.magic_bag.seller != request.user:
                return Response({'error': 'این سفارش متعلق به شما نیست.'}, status=status.HTTP_403_FORBIDDEN)

        if order.status != Order.OrderStatus.PENDING_PAYMENT:
            return Response({'error': 'فقط سفارش‌های در انتظار قابل رد هستند.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # Restore inventory when rejecting
            bag = MagicBag.objects.select_for_update().get(id=order.magic_bag_id)
            bag.quantity += order.quantity
            bag.save()

            order.status = Order.OrderStatus.CANCELLED
            order.save()

        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)


class VerifyPickupView(APIView):
    """Seller scans buyer's pickup code → PICKED_UP (انجام شده)."""
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, pk):
        pickup_code = request.data.get('pickup_code')
        if not pickup_code:
            return Response({'error': 'کد تحویل الزامی است.'}, status=status.HTTP_400_BAD_REQUEST)

        pickup_code = str(pickup_code).strip().upper()
        order = get_object_or_404(Order, id=pk)

        # Verify seller permission (either store owner or individual seller)
        if order.magic_bag.store:
            try:
                store = request.user.store
                if order.magic_bag.store != store:
                    return Response({'error': 'این سفارش متعلق به فروشگاه شما نیست.'}, status=status.HTTP_403_FORBIDDEN)
            except (AttributeError, Store.DoesNotExist):
                return Response({'error': 'شما دسترسی به فروشگاهی ندارید.'}, status=status.HTTP_403_FORBIDDEN)
        else:
            if order.magic_bag.seller != request.user:
                return Response({'error': 'این سفارش متعلق به شما نیست.'}, status=status.HTTP_403_FORBIDDEN)

        if order.pickup_code != pickup_code:
            return Response({'error': 'کد تحویل نامعتبر است.'}, status=status.HTTP_400_BAD_REQUEST)

        if order.status == Order.OrderStatus.PICKED_UP:
            return Response({'error': 'این سفارش قبلاً تحویل داده شده است.'}, status=status.HTTP_400_BAD_REQUEST)

        if order.status != Order.OrderStatus.PAID:
            return Response({'error': 'سفارش باید ابتدا تایید شده باشد.'}, status=status.HTTP_400_BAD_REQUEST)

        if order.status == Order.OrderStatus.CANCELLED:
            return Response({'error': 'این سفارش لغو شده است.'}, status=status.HTTP_400_BAD_REQUEST)

        order.status = Order.OrderStatus.PICKED_UP
        order.save()

        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)


class VendorOrdersView(APIView):
    """List all orders for the authenticated seller (both store orders and individual orders)."""
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        from django.db.models import Q
        
        # Query orders where either the bag belongs to the user's store, or the user is the direct seller
        orders = Order.objects.filter(
            Q(magic_bag__store__owner=request.user) | Q(magic_bag__seller=request.user)
        ).order_by('-created_at')
        
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

