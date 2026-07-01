import threading
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITransactionTestCase, APITestCase
from stores.models import Store
from inventory.models import MagicBag
from orders.models import Order

User = get_user_model()


class OrdersIntegrationTests(APITransactionTestCase):
    """Integration tests for Orders, Concurrency, and Pickup Verification."""

    def setUp(self):
        # Create a Vendor User and approved store
        self.vendor_user = User.objects.create_user(
            phone_number='09121111111',
            role='VENDOR'
        )
        self.store = Store.objects.create(
            owner=self.vendor_user,
            name='فروشگاه تایید شده',
            address='آدرس',
            latitude=35.6892,
            longitude=51.3890,
            status=Store.StoreStatus.APPROVED
        )

        # Create a customer user
        self.customer_user = User.objects.create_user(
            phone_number='09122222222',
            role='CUSTOMER'
        )

        # Create MagicBag
        self.magic_bag = MagicBag.objects.create(
            store=self.store,
            original_price='100000.00',
            platform_price='30000.00',
            quantity=2, # Initial stock is 2
            pickup_start_time='18:00:00',
            pickup_end_time='20:00:00'
        )

        self.order_url = reverse('order_create')

    def tearDown(self):
        Order.objects.all().delete()
        MagicBag.objects.all().delete()
        Store.objects.all().delete()
        User.objects.all().delete()

    def test_concurrent_orders_prevent_overselling(self):
        """Simulate concurrent order placements to verify select_for_update locks.
        Under SQLite, we fallback to a sequential depletion check due to SQLite's lack of concurrent write transactions.
        """
        from django.db import connection
        if connection.vendor == 'sqlite':
            # Sequential depletion test under SQLite
            user1 = User.objects.create_user(phone_number='09123333331', role='CUSTOMER')
            self.client.force_authenticate(user=user1)
            response1 = self.client.post(self.order_url, {'magic_bag': self.magic_bag.id, 'quantity': 1}, format='json')
            self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

            user2 = User.objects.create_user(phone_number='09123333332', role='CUSTOMER')
            self.client.force_authenticate(user=user2)
            response2 = self.client.post(self.order_url, {'magic_bag': self.magic_bag.id, 'quantity': 1}, format='json')
            self.assertEqual(response2.status_code, status.HTTP_201_CREATED)

            user3 = User.objects.create_user(phone_number='09123333333', role='CUSTOMER')
            self.client.force_authenticate(user=user3)
            response3 = self.client.post(self.order_url, {'magic_bag': self.magic_bag.id, 'quantity': 1}, format='json')
            self.assertEqual(response3.status_code, status.HTTP_400_BAD_REQUEST)

            self.magic_bag.refresh_from_db()
            self.assertEqual(self.magic_bag.quantity, 0)
            return

        # True concurrent multi-threaded test (runs on Postgres/Docker)
        users = []
        for i in range(3):
            u = User.objects.create_user(
                phone_number=f'0912333333{i}',
                role='CUSTOMER'
            )
            users.append(u)

        results = []
        threads = []

        def place_order(user):
            from rest_framework.test import APIClient
            from django.db import utils, connections
            connections.close_all()
            client = APIClient()
            client.force_authenticate(user=user)
            try:
                response = client.post(self.order_url, {'magic_bag': self.magic_bag.id, 'quantity': 1}, format='json')
                results.append(response)
            except utils.OperationalError:
                results.append('LOCKED')
            except Exception as e:
                results.append(e)
            finally:
                try:
                    connections.close_all()
                except Exception:
                    pass

        for u in users:
            t = threading.Thread(target=place_order, args=(u,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        success_count = sum(1 for r in results if hasattr(r, 'status_code') and r.status_code == status.HTTP_201_CREATED)
        self.assertLessEqual(success_count, 2)
        self.magic_bag.refresh_from_db()
        self.assertEqual(self.magic_bag.quantity, 2 - success_count)
        self.assertGreaterEqual(self.magic_bag.quantity, 0)

    def test_order_state_transitions(self):
        """Test the state transition from created -> paid -> picked up with validation checks."""
        # Authenticate customer
        self.client.force_authenticate(user=self.customer_user)

        # Place order
        response = self.client.post(self.order_url, {'magic_bag': self.magic_bag.id, 'quantity': 1}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        order_id = response.data['id']
        pickup_code = response.data['pickup_code']

        # Initial status should be PENDING_PAYMENT
        order = Order.objects.get(id=order_id)
        self.assertEqual(order.status, Order.OrderStatus.PENDING_PAYMENT)

        # 1. Try to verify pickup when not paid and with incorrect code -> fails
        verify_url = reverse('order_verify_pickup', kwargs={'pk': order_id})
        self.client.force_authenticate(user=self.vendor_user)
        response_verify = self.client.post(verify_url, {'pickup_code': 'WRONG'}, format='json')
        self.assertEqual(response_verify.status_code, status.HTTP_400_BAD_REQUEST)

        # 2. Try to verify pickup from a user who is not the store owner -> fails
        non_owner = User.objects.create_user(phone_number='09129999999', role='VENDOR')
        self.client.force_authenticate(user=non_owner)
        response_verify = self.client.post(verify_url, {'pickup_code': pickup_code}, format='json')
        self.assertEqual(response_verify.status_code, status.HTTP_403_FORBIDDEN)

        # 3. Simulate vendor approving the order
        self.client.force_authenticate(user=self.vendor_user)
        approve_url = reverse('order_approve', kwargs={'pk': order_id})
        response_approve = self.client.post(approve_url, format='json')
        self.assertEqual(response_approve.status_code, status.HTTP_200_OK)
        self.assertEqual(response_approve.data['status'], Order.OrderStatus.PAID)

        # 4. Verify pickup with correct code from the actual store owner -> succeeds
        response_verify = self.client.post(verify_url, {'pickup_code': pickup_code}, format='json')
        self.assertEqual(response_verify.status_code, status.HTTP_200_OK)
        self.assertEqual(response_verify.data['status'], Order.OrderStatus.PICKED_UP)

    def test_order_rejection_restores_inventory(self):
        """Test order rejection by vendor and inventory restoration."""
        self.client.force_authenticate(user=self.customer_user)
        response = self.client.post(self.order_url, {'magic_bag': self.magic_bag.id, 'quantity': 1}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        order_id = response.data['id']

        # Stock should be decremented by 1 (initial was 2, now 1)
        self.magic_bag.refresh_from_db()
        self.assertEqual(self.magic_bag.quantity, 1)

        # Vendor rejects order
        self.client.force_authenticate(user=self.vendor_user)
        reject_url = reverse('order_reject', kwargs={'pk': order_id})
        response_reject = self.client.post(reject_url, format='json')
        self.assertEqual(response_reject.status_code, status.HTTP_200_OK)
        self.assertEqual(response_reject.data['status'], Order.OrderStatus.CANCELLED)

        # Stock should be restored to 2
        self.magic_bag.refresh_from_db()
        self.assertEqual(self.magic_bag.quantity, 2)

    def test_individual_seller_order_lifecycle(self):
        """Test order placement, approval, rejection, and verification on individual products (no store)."""
        # Create an individual product (store is None, seller is vendor_user)
        indiv_bag = MagicBag.objects.create(
            store=None,
            seller=self.vendor_user,
            name='غذای خانگی فردی',
            category=MagicBag.CategoryChoices.FOODS,
            latitude=35.6892,
            longitude=51.3890,
            original_price='120000.00',
            platform_price='40000.00',
            quantity=5,
            pickup_start_time='12:00:00',
            pickup_end_time='14:00:00'
        )

        # 1. Place order as customer
        self.client.force_authenticate(user=self.customer_user)
        response = self.client.post(self.order_url, {'magic_bag': indiv_bag.id, 'quantity': 1}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        order_id = response.data['id']
        pickup_code = response.data['pickup_code']

        # 2. Try to approve order as a different vendor -> fails
        other_vendor = User.objects.create_user(phone_number='09128888888', role='VENDOR')
        self.client.force_authenticate(user=other_vendor)
        approve_url = reverse('order_approve', kwargs={'pk': order_id})
        response_approve = self.client.post(approve_url, format='json')
        self.assertEqual(response_approve.status_code, status.HTTP_403_FORBIDDEN)

        # 3. Approve order as the actual individual seller (vendor_user) -> succeeds
        self.client.force_authenticate(user=self.vendor_user)
        response_approve = self.client.post(approve_url, format='json')
        self.assertEqual(response_approve.status_code, status.HTTP_200_OK)
        self.assertEqual(response_approve.data['status'], Order.OrderStatus.PAID)

        # 4. Verify pickup as the individual seller -> succeeds
        verify_url = reverse('order_verify_pickup', kwargs={'pk': order_id})
        response_verify = self.client.post(verify_url, {'pickup_code': pickup_code}, format='json')
        self.assertEqual(response_verify.status_code, status.HTTP_200_OK)
        self.assertEqual(response_verify.data['status'], Order.OrderStatus.PICKED_UP)


class ProximitySearchTests(APITestCase):
    """Tests for available magic bags proximity calculation and sorting."""

    def setUp(self):
        # Create vendor and store A (Tehran center)
        self.vendor_a = User.objects.create_user(phone_number='09127777771', role='VENDOR')
        self.store_a = Store.objects.create(
            owner=self.vendor_a, name='فروشگاه مرکز', address='مرکز تهران',
            latitude=35.6892, longitude=51.3890, status=Store.StoreStatus.APPROVED
        )
        self.bag_a = MagicBag.objects.create(
            store=self.store_a, original_price='100000.00', platform_price='30000.00',
            quantity=5, pickup_start_time='18:00:00', pickup_end_time='20:00:00'
        )

        # Create vendor and store B (Near center)
        self.vendor_b = User.objects.create_user(phone_number='09127777772', role='VENDOR')
        self.store_b = Store.objects.create(
            owner=self.vendor_b, name='فروشگاه نزدیک', address='نزدیک مرکز',
            latitude=35.7000, longitude=51.4000, status=Store.StoreStatus.APPROVED
        )
        self.bag_b = MagicBag.objects.create(
            store=self.store_b, original_price='100000.00', platform_price='30000.00',
            quantity=5, pickup_start_time='18:00:00', pickup_end_time='20:00:00'
        )

        # Create vendor and store C (Far away but within 10km limit)
        self.vendor_c = User.objects.create_user(phone_number='09127777773', role='VENDOR')
        self.store_c = Store.objects.create(
            owner=self.vendor_c, name='فروشگاه دور', address='حومه تهران',
            latitude=35.7200, longitude=51.4200, status=Store.StoreStatus.APPROVED
        )
        self.bag_c = MagicBag.objects.create(
            store=self.store_c, original_price='100000.00', platform_price='30000.00',
            quantity=5, pickup_start_time='18:00:00', pickup_end_time='20:00:00'
        )

        self.available_url = reverse('available_magic_bags')

    def tearDown(self):
        MagicBag.objects.all().delete()
        Store.objects.all().delete()
        User.objects.all().delete()

    def test_proximity_sorting_returns_nearest_first(self):
        # Query passing coordinates close to Store A (center)
        response = self.client.get(self.available_url, {'latitude': 35.6892, 'longitude': 51.3890})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data

        # We should receive 3 items, sorted A -> B -> C
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]['id'], self.bag_a.id)
        self.assertEqual(results[1]['id'], self.bag_b.id)
        self.assertEqual(results[2]['id'], self.bag_c.id)

        # Distance should be annotated
        self.assertEqual(results[0]['distance'], 0.0)
        self.assertGreater(results[1]['distance'], 0.0)
        self.assertGreater(results[2]['distance'], results[1]['distance'])
