from django.db import models
from django.conf import settings


class UserAddress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='addresses')
    name = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=12, decimal_places=6)
    longitude = models.DecimalField(max_digits=12, decimal_places=6)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def set_as_active(self):
        """Deactivate all other addresses for this user and activate this one."""
        UserAddress.objects.filter(user=self.user).update(is_active=False)
        self.is_active = True
        self.save(update_fields=['is_active'])

    def __str__(self):
        return f"{self.name} ({self.latitude}, {self.longitude})"

    def distance_to(self, lat, lng):
        """Return distance in km using Haversine formula."""
        from math import radians, cos, sin, asin, sqrt
        r = 6371  # Earth radius in km
        lat1, lon1 = radians(float(self.latitude)), radians(float(self.longitude))
        lat2, lon2 = radians(lat), radians(lng)
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        return r * c


class Store(models.Model):
    class StoreStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'

    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='store'
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    address = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    status = models.CharField(
        max_length=10,
        choices=StoreStatus.choices,
        default=StoreStatus.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.status})"
