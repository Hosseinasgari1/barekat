import random
import logging
from django.core.cache import cache

logger = logging.getLogger(__name__)


def generate_otp():
    """Generates a random 5-digit OTP."""
    return "".join(random.choices("0123456789", k=5))


def store_otp(phone_number, otp):
    """Stores the OTP in the Django cache with a 2-minute (120 seconds) TTL."""
    key = f"otp:{phone_number}"
    cache.set(key, str(otp), timeout=120)


def verify_otp(phone_number, otp):
    """Verifies the OTP against the value stored in the Django cache.
    If valid, deletes the OTP from cache and returns True.
    """
    key = f"otp:{phone_number}"
    stored_otp = cache.get(key)
    if stored_otp is not None:
        if str(stored_otp) == str(otp):
            cache.delete(key)
            return True
    return False


def send_mock_sms(phone_number, otp):
    """Mock SMS sender logging the OTP to the console."""
    print(f"\n=========================================")
    print(f"[MOCK SMS] OTP: {otp} -> Phone: {phone_number}")
    print(f"=========================================\n")
    logger.info(f"[MOCK SMS SENDER] Sent OTP {otp} to {phone_number}")
