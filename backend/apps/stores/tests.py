from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from stores.models import Store

User = get_user_model()


class StoreIntegrationTests(APITestCase):
    def setUp(self):
        # Create a Vendor User
        self.vendor_user = User.objects.create_user(
            phone_number='09120000001',
            role='VENDOR'
        )
        # Create a Customer User
        self.customer_user = User.objects.create_user(
            phone_number='09120000002',
            role='CUSTOMER'
        )
        self.store_profile_url = reverse('store_profile')
        self.my_store_url = reverse('my_store')

    def tearDown(self):
        Store.objects.all().delete()
        User.objects.all().delete()

    def test_vendor_can_create_and_update_store(self):
        self.client.force_authenticate(user=self.vendor_user)
        
        # Test creation
        store_data = {
            'name': 'فروشگاه برکت تست',
            'description': 'توضیحات تست فروشگاه',
            'address': 'تهران، خیابان تست',
            'latitude': 35.6892,
            'longitude': 51.3890
        }
        response = self.client.post(self.store_profile_url, store_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], store_data['name'])
        self.assertEqual(response.data['status'], Store.StoreStatus.PENDING)
        
        # Test retrieve
        response_get = self.client.get(self.my_store_url)
        self.assertEqual(response_get.status_code, status.HTTP_200_OK)
        self.assertEqual(response_get.data['name'], store_data['name'])

    def test_unauthenticated_user_is_denied_store_access(self):
        store_data = {
            'name': 'فروشگاه غیرمجاز',
            'address': 'تهران',
            'latitude': 35.6892,
            'longitude': 51.3890
        }
        
        response_post = self.client.post(self.store_profile_url, store_data, format='json')
        self.assertEqual(response_post.status_code, status.HTTP_401_UNAUTHORIZED)
        
        response_get = self.client.get(self.my_store_url)
        self.assertEqual(response_get.status_code, status.HTTP_401_UNAUTHORIZED)

