from unittest.mock import patch, MagicMock
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class OTPIntegrationTests(APITestCase):
    def setUp(self):
        # Setup mock cache
        self.mock_cache = MagicMock()
        self.mock_cache_patcher = patch('users.otp.cache', self.mock_cache)
        self.mock_cache = self.mock_cache_patcher.start()
        
        self.send_otp_url = reverse('send_otp')
        self.verify_otp_url = reverse('verify_otp')
        self.phone_number = '09123456789'
        self.otp = '12345'

    def tearDown(self):
        self.mock_cache_patcher.stop()
        User.objects.all().delete()

    def test_send_otp_successful(self):
        data = {'phone_number': self.phone_number}
        response = self.client.post(self.send_otp_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('detail', response.data)
        
        # Verify stored in cache
        self.mock_cache.set.assert_called_once()
        call_args = self.mock_cache.set.call_args[0]
        self.assertEqual(call_args[0], f"otp:{self.phone_number}")
        self.assertEqual(len(call_args[1]), 5)  # 5 digit OTP
        self.assertEqual(self.mock_cache.set.call_args[1]['timeout'], 120)  # 2 minute TTL

    def test_send_otp_invalid_phone_number(self):
        invalid_phones = ['12345', '0912abc5678', '08123456789', '+98123456']
        for phone in invalid_phones:
            data = {'phone_number': phone}
            response = self.client.post(self.send_otp_url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn('error', response.data)

    def test_verify_otp_successful_and_user_creation(self):
        # Mock cache returning valid OTP
        self.mock_cache.get.return_value = self.otp
        
        data = {
            'phone_number': self.phone_number,
            'otp': self.otp
        }
        
        # Verify user does not exist yet
        self.assertFalse(User.objects.filter(phone_number=self.phone_number).exists())
        
        response = self.client.post(self.verify_otp_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['phone_number'], self.phone_number)
        self.assertEqual(response.data['user']['role'], User.Roles.CUSTOMER)
        
        # Verify user was created
        self.assertTrue(User.objects.filter(phone_number=self.phone_number).exists())
        created_user = User.objects.get(phone_number=self.phone_number)
        self.assertEqual(created_user.role, User.Roles.CUSTOMER)
        
        # Verify OTP was deleted from cache
        self.mock_cache.delete.assert_called_once_with(f"otp:{self.phone_number}")

    def test_verify_otp_failure_with_wrong_code(self):
        # Mock cache returning different OTP or None
        self.mock_cache.get.return_value = '54321'
        
        data = {
            'phone_number': self.phone_number,
            'otp': self.otp
        }
        
        response = self.client.post(self.verify_otp_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertFalse(User.objects.filter(phone_number=self.phone_number).exists())
