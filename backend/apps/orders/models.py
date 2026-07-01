from django.db import models
from django.conf import settings
import random
import string


class Order(models.Model):
    class OrderStatus(models.TextChoices):
        PENDING_PAYMENT = 'PENDING_PAYMENT', 'Pending Payment'
        PAID = 'PAID', 'Paid'
        PICKED_UP = 'PICKED_UP', 'Picked Up'
        CANCELLED = 'CANCELLED', 'Cancelled'

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    magic_bag = models.ForeignKey(
        'inventory.MagicBag',
        on_delete=models.CASCADE,
        related_name='orders'
    )
    quantity = models.IntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING_PAYMENT
    )
    pickup_code = models.CharField(max_length=6, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.id} - {self.customer.phone_number} - {self.status}"
