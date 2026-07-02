from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from math import radians, cos, sin, asin, sqrt

from inventory.models import MagicBag
from inventory.serializers import MagicBagSerializer, AvailableMagicBagSerializer
from stores.permissions import IsVendor, IsApprovedVendor, CanListProduct
from stores.models import Store, UserAddress


def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance in kilometers between two points
    on the earth (specified in decimal degrees)
    """
    lon1, lat1, lon2, lat2 = map(radians, [float(lon1), float(lat1), float(lon2), float(lat2)])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Earth radius in kilometers
    return c * r


class MagicBagListCreateView(generics.ListCreateAPIView):
    """API view to list or create MagicBags for the authenticated vendor or individual seller."""
    serializer_class = MagicBagSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated(), CanListProduct()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        from django.db.models import Q
        # Return bags belonging to their store OR listed by them directly
        return MagicBag.objects.filter(
            Q(store__owner=self.request.user) | Q(seller=self.request.user)
        )

    def perform_create(self, serializer):
        try:
            store = self.request.user.store
            serializer.save(store=store, seller=self.request.user)
        except (Store.DoesNotExist, AttributeError):
            # Individual seller listing (no store)
            lat = self.request.data.get('latitude')
            lng = self.request.data.get('longitude')
            
            # Fallback to active address coordinates if none provided
            if not lat or not lng:
                active_addr = UserAddress.objects.filter(user=self.request.user, is_active=True).first()
                if active_addr:
                    lat = active_addr.latitude
                    lng = active_addr.longitude
            
            serializer.save(store=None, seller=self.request.user, latitude=lat, longitude=lng)


class AvailableMagicBagsView(APIView):
    """API view for public or customers to fetch active magic bags/products.
    Supports category filtering.
    Sorts bags by distance if latitude and longitude parameters are present.
    """
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        from django.db.models import Q
        
        # Bags belonging to APPROVED stores OR individual sellers, and approved by admin
        bags = MagicBag.objects.filter(
            Q(store__status='APPROVED') | Q(store__isnull=True),
            approval_status='APPROVED',
            is_active=True,
            quantity__gt=0
        ).select_related('store', 'seller')

        # Filter by category if requested
        category = request.query_params.get('category')
        if category:
            bags = bags.filter(category=category)

        lat_param = request.query_params.get('latitude')
        lng_param = request.query_params.get('longitude')

        if lat_param and lng_param:
            try:
                user_lat = float(lat_param)
                user_lng = float(lng_param)

                # Compute distance for each bag and keep only those within 10km
                results = []
                for bag in bags:
                    if bag.store:
                        bag_lat = bag.store.latitude
                        bag_lng = bag.store.longitude
                    else:
                        bag_lat = bag.latitude
                        bag_lng = bag.longitude
                    
                    if bag_lat is None or bag_lng is None:
                        continue
                        
                    dist = haversine(user_lng, user_lat, bag_lng, bag_lat)
                    if dist <= 10:
                        bag.distance = round(dist, 2)
                        results.append(bag)

                # Sort nearest first
                results.sort(key=lambda x: x.distance)
                serializer = AvailableMagicBagSerializer(results, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except ValueError:
                pass

        # No coordinates provided — return empty list so buyer must pick an address
        return Response([], status=status.HTTP_200_OK)


class IsAdminUser(permissions.BasePermission):
    """Allows access only to admin users."""
    def has_permission(self, request, view):
        return request.user and (request.user.role == 'ADMIN' or request.user.is_staff)


class AdminPendingBagsListView(generics.ListAPIView):
    """List all pending magic bags for admin approval."""
    queryset = MagicBag.objects.filter(approval_status='PENDING')
    serializer_class = AvailableMagicBagSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    pagination_class = None


class AdminApproveRejectBagView(APIView):
    """Approve or reject a magic bag."""
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]

    def post(self, request, pk):
        try:
            bag = MagicBag.objects.get(pk=pk)
        except MagicBag.DoesNotExist:
            return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
            
        action = request.data.get('action')
        if action == 'approve':
            bag.approval_status = 'APPROVED'
            bag.save()
            return Response({"detail": "Product approved successfully."}, status=status.HTTP_200_OK)
        elif action == 'reject':
            bag.approval_status = 'REJECTED'
            bag.save()
            return Response({"detail": "Product rejected successfully."}, status=status.HTTP_200_OK)
        
        return Response({"detail": "Invalid action."}, status=status.HTTP_400_BAD_REQUEST)

