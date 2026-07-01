from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from stores.models import Store
from stores.serializers import StoreSerializer
from stores.permissions import IsVendor

from rest_framework import viewsets
from rest_framework.decorators import action

from .models import UserAddress, Store
from .serializers import UserAddressSerializer, StoreSerializer


class StoreProfileView(APIView):
    """API view to create or update the authenticated vendor's store details."""
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        try:
            store = request.user.store
            serializer = StoreSerializer(store, data=request.data, partial=True)
            created = False
        except Store.DoesNotExist:
            store = None
            serializer = StoreSerializer(data=request.data)
            created = True

        if serializer.is_valid():
            status_val = request.data.get('status')
            if status_val in Store.StoreStatus.values:
                serializer.save(owner=request.user, status=status_val)
            else:
                serializer.save(owner=request.user)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MyStoreView(APIView):
    """API view to retrieve the authenticated vendor's store details."""
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        try:
            store = request.user.store
            serializer = StoreSerializer(store)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Store.DoesNotExist:
            return Response(
                {'detail': 'فروشگاهی یافت نشد.'},
                status=status.HTTP_404_NOT_FOUND
            )


class UserAddressViewSet(viewsets.ModelViewSet):
    """CRUD for user addresses. The active address is stored server-side via is_active flag."""
    queryset = UserAddress.objects.all()
    serializer_class = UserAddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Save new address. If it is the user's first address, make it active automatically."""
        user = self.request.user
        is_first = not UserAddress.objects.filter(user=user).exists()
        instance = serializer.save(user=user, is_active=is_first)
        # If first address, mark as active (is_active already True from above)
        # If not first, leave existing active address unchanged

    @action(detail=True, methods=['post'], url_path='set-active')
    def set_active(self, request, pk=None):
        """Set this address as the user's active address (deactivates all others)."""
        address = self.get_object()
        address.set_as_active()
        serializer = self.get_serializer(address)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='active')
    def get_active(self, request):
        """Return the currently active address for the authenticated user."""
        try:
            address = UserAddress.objects.get(user=request.user, is_active=True)
            serializer = self.get_serializer(address)
            return Response(serializer.data)
        except UserAddress.DoesNotExist:
            return Response(None)

    @action(detail=True, methods=['get'], url_path='nearby-stores')
    def nearby_stores(self, request, pk=None):
        """Return stores within 10km of the address."""
        address = self.get_object()
        nearby = []
        for store in Store.objects.all():
            dist = address.distance_to(float(store.latitude), float(store.longitude))
            if dist <= 10:
                nearby.append(store)
        serializer = StoreSerializer(nearby, many=True)
        return Response(serializer.data)
