from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from stores.models import Store
from inventory.models import MagicBag

User = get_user_model()


class InventoryIntegrationTests(APITestCase):
    def setUp(self):
        # Create an Approved Vendor User and store
        self.approved_vendor = User.objects.create_user(
            phone_number='09121111111',
            role='VENDOR'
        )
        self.approved_store = Store.objects.create(
            owner=self.approved_vendor,
            name='فروشگاه تایید شده',
            address='آدرس',
            latitude=35.6892,
            longitude=51.3890,
            status=Store.StoreStatus.APPROVED
        )

        # Create a Pending Vendor User and store
        self.pending_vendor = User.objects.create_user(
            phone_number='09122222222',
            role='VENDOR'
        )
        self.pending_store = Store.objects.create(
            owner=self.pending_vendor,
            name='فروشگاه معلق',
            address='آدرس',
            latitude=35.6892,
            longitude=51.3890,
            status=Store.StoreStatus.PENDING
        )

        self.bags_url = reverse('magic_bags')
        self.bag_data = {
            'original_price': '100000.00',
            'platform_price': '30000.00',
            'quantity': 5,
            'pickup_start_time': '18:00:00',
            'pickup_end_time': '20:00:00'
        }

    def tearDown(self):
        MagicBag.objects.all().delete()
        Store.objects.all().delete()
        User.objects.all().delete()

    def test_approved_vendor_can_create_magic_bag(self):
        self.client.force_authenticate(user=self.approved_vendor)
        
        response = self.client.post(self.bags_url, self.bag_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(MagicBag.objects.filter(store=self.approved_store).count(), 1)
        
        # Test listing
        response_list = self.client.get(self.bags_url)
        self.assertEqual(response_list.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_list.data['results']), 1)

    def test_pending_vendor_cannot_create_magic_bag(self):
        self.client.force_authenticate(user=self.pending_vendor)
        
        response = self.client.post(self.bags_url, self.bag_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(MagicBag.objects.filter(store=self.pending_store).count(), 0)
