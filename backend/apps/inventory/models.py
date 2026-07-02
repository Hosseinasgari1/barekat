from django.db import models
from django.conf import settings


class MagicBag(models.Model):
    class CategoryChoices(models.TextChoices):
        VEGETABLES = 'VEGETABLES', 'میوه و سبزیجات'
        SWEETS = 'SWEETS', 'شیرینی و دسر'
        FOODS = 'FOODS', 'غذاهای آماده'
        SUPERMARKET = 'SUPERMARKET', 'سوپرمارکت'
        RESTAURANT = 'RESTAURANT', 'رستوران و فست‌فود'
        BAKERY = 'BAKERY', 'نان و نانوایی'
        BEVERAGES = 'BEVERAGES', 'نوشیدنی‌ها'
        INGREDIENTS = 'INGREDIENTS', 'مواد اولیه'
        OTHER = 'OTHER', 'سایر'

    store = models.ForeignKey(
        'stores.Store',
        on_delete=models.CASCADE,
        related_name='magic_bags',
        null=True,
        blank=True
    )
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='individual_bags',
        null=True,
        blank=True
    )
    name = models.CharField(max_length=255, default='کیسه جادویی')
    description = models.TextField(blank=True, default='')
    category = models.CharField(
        max_length=50,
        choices=CategoryChoices.choices,
        default=CategoryChoices.FOODS
    )
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    image = models.FileField(upload_to='bags/', null=True, blank=True)
    expiry_image = models.FileField(upload_to='expiry_labels/', null=True, blank=True)
    approval_status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('APPROVED', 'Approved'),
            ('REJECTED', 'Rejected')
        ],
        default='PENDING'
    )

    original_price = models.DecimalField(max_digits=10, decimal_places=2)
    platform_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()
    pickup_start_time = models.TimeField()
    pickup_end_time = models.TimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        store_name = self.store.name if self.store else f"Individual ({self.seller.phone_number if self.seller else self.id})"
        return f"{self.name} (ID: {self.id}) - Store: {store_name} (Qty: {self.quantity})"

