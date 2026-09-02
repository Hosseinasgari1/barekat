from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Avg, Count, Q
from math import radians, cos, sin, asin, sqrt

from inventory.models import MagicBag, MasterProduct
from inventory.serializers import MagicBagSerializer, AvailableMagicBagSerializer, MasterProductSerializer
from stores.permissions import IsVendor, IsApprovedVendor, CanListProduct
from stores.models import Store, UserAddress
from orders.models import Review

class MasterCatalogSearchView(generics.ListAPIView):
    """
    API view for searching products in the master catalog.
    Used by sellers to find standard products when creating a Magic Bag.
    """
    serializer_class = MasterProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        query = self.request.query_params.get('q', '').strip()
        if not query:
            return MasterProduct.objects.none()
        return MasterProduct.objects.filter(title__icontains=query)[:20]


class CatalogSourcesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        sources = MasterProduct.objects.values_list('source', flat=True).distinct()
        return Response([s for s in sources if s], status=status.HTTP_200_OK)


class CatalogCategoriesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        source = request.query_params.get('source')
        qs = MasterProduct.objects.all()
        if source:
            qs = qs.filter(source=source)
        
        categories = qs.values_list('category', flat=True).distinct()
        return Response([c for c in categories if c], status=status.HTTP_200_OK)


from rest_framework.pagination import PageNumberPagination

class CatalogProductPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class CatalogProductsView(generics.ListAPIView):
    serializer_class = MasterProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CatalogProductPagination

    def get_queryset(self):
        qs = MasterProduct.objects.all()
        source = self.request.query_params.get('source')
        category = self.request.query_params.get('category')
        
        if source:
            qs = qs.filter(source=source)
        if category:
            qs = qs.filter(category=category)
            
        return qs.order_by('title')



def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(radians, [float(lon1), float(lat1), float(lon2), float(lat2)])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Earth radius in kilometers
    return c * r


def _build_seller_rating_maps():
    """Return (store_ratings, seller_ratings) dicts keyed by id -> (avg, count)."""
    store_rows = (
        Review.objects.filter(order__magic_bag__store__isnull=False)
        .values('order__magic_bag__store_id')
        .annotate(average_rating=Avg('rating'), review_count=Count('id'))
    )
    store_ratings = {
        row['order__magic_bag__store_id']: (
            round(row['average_rating'], 1),
            row['review_count'],
        )
        for row in store_rows
    }

    seller_rows = (
        Review.objects.filter(order__magic_bag__store__isnull=True)
        .values('order__magic_bag__seller_id')
        .annotate(average_rating=Avg('rating'), review_count=Count('id'))
    )
    seller_ratings = {
        row['order__magic_bag__seller_id']: (
            round(row['average_rating'], 1),
            row['review_count'],
        )
        for row in seller_rows
    }
    return store_ratings, seller_ratings


def _attach_seller_ratings(bags, store_ratings, seller_ratings):
    for bag in bags:
        if bag.store_id:
            avg, count = store_ratings.get(bag.store_id, (None, 0))
        else:
            avg, count = seller_ratings.get(bag.seller_id, (None, 0))
        bag.seller_rating = avg
        bag.seller_rating_count = count
    return bags


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

        store_ratings, seller_ratings = _build_seller_rating_maps()
        sort_mode = request.query_params.get('sort', 'distance')

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

                _attach_seller_ratings(results, store_ratings, seller_ratings)

                if sort_mode == 'rating':
                    results.sort(
                        key=lambda x: (
                            -(x.seller_rating or 0),
                            x.distance,
                        )
                    )
                else:
                    results.sort(key=lambda x: x.distance)

                serializer = AvailableMagicBagSerializer(results, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except ValueError:
                pass

        # No coordinates provided — return empty list so buyer must pick an address
        return Response([], status=status.HTTP_200_OK)


class IsAdminUser(permissions.BasePermission):
    """Allows access only to admins who can approve products.

    A super admin always passes; a sub-admin must have the
    'approve_products' permission in their admin_permissions list.
    """
    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated and user.role == 'ADMIN'):
            return False
        if getattr(user, 'is_super_admin', False):
            return True
        return 'approve_products' in (getattr(user, 'admin_permissions', None) or [])



class AdminPendingBagsListView(generics.ListAPIView):
    """List all pending magic bags for admin approval."""
    queryset = MagicBag.objects.filter(approval_status='PENDING').select_related('store', 'seller')
    serializer_class = AvailableMagicBagSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    pagination_class = None


class AdminBagsListView(generics.ListAPIView):
    """List magic bags for admin management.

    Optional query param ``status``: PENDING | APPROVED | REJECTED | ALL (default ALL).
    """
    serializer_class = AvailableMagicBagSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    pagination_class = None

    def get_queryset(self):
        qs = MagicBag.objects.select_related('store', 'seller').all()
        status_filter = (self.request.query_params.get('status') or 'ALL').upper()
        if status_filter in ('PENDING', 'APPROVED', 'REJECTED'):
            qs = qs.filter(approval_status=status_filter)
        return qs


class AdminApproveRejectBagView(APIView):
    """Manage a magic bag from the admin panel.

    Supported actions:
      - approve / reject / reopen
      - activate / deactivate
      - set_quantity (body: quantity)
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]

    def post(self, request, pk):
        try:
            bag = MagicBag.objects.select_related('store', 'seller').get(pk=pk)
        except MagicBag.DoesNotExist:
            return Response({"detail": "محصول یافت نشد."}, status=status.HTTP_404_NOT_FOUND)

        action = request.data.get('action')

        if action == 'approve':
            bag.approval_status = 'APPROVED'
            bag.is_active = True
            bag.save(update_fields=['approval_status', 'is_active', 'updated_at'])
            return Response({"detail": "محصول با موفقیت تایید شد."}, status=status.HTTP_200_OK)

        if action == 'reject':
            bag.approval_status = 'REJECTED'
            bag.is_active = False
            bag.save(update_fields=['approval_status', 'is_active', 'updated_at'])
            return Response({"detail": "محصول رد شد."}, status=status.HTTP_200_OK)

        if action == 'reopen':
            bag.approval_status = 'PENDING'
            bag.save(update_fields=['approval_status', 'updated_at'])
            return Response({"detail": "محصول به صف بررسی بازگشت."}, status=status.HTTP_200_OK)

        if action == 'activate':
            if bag.approval_status != 'APPROVED':
                return Response(
                    {"detail": "فقط محصولات تاییدشده قابل فعال‌سازی هستند."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            bag.is_active = True
            bag.save(update_fields=['is_active', 'updated_at'])
            return Response({"detail": "محصول فعال شد."}, status=status.HTTP_200_OK)

        if action == 'deactivate':
            bag.is_active = False
            bag.save(update_fields=['is_active', 'updated_at'])
            return Response({"detail": "محصول غیرفعال شد."}, status=status.HTTP_200_OK)

        if action == 'set_quantity':
            quantity = request.data.get('quantity')
            try:
                quantity = int(quantity)
            except (TypeError, ValueError):
                return Response({"detail": "تعداد نامعتبر است."}, status=status.HTTP_400_BAD_REQUEST)
            if quantity < 0:
                return Response({"detail": "تعداد نمی‌تواند منفی باشد."}, status=status.HTTP_400_BAD_REQUEST)
            bag.quantity = quantity
            bag.save(update_fields=['quantity', 'updated_at'])
            return Response(
                {"detail": "موجودی به‌روزرسانی شد.", "quantity": bag.quantity},
                status=status.HTTP_200_OK,
            )

        return Response({"detail": "عملیات نامعتبر است."}, status=status.HTTP_400_BAD_REQUEST)

