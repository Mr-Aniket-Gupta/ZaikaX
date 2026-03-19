from django.db import models
from django.conf import settings
from accounts.models import Address


class PaymentSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    cashfree_order_id = models.CharField(max_length=200, unique=True)
    payment_session_id = models.CharField(max_length=200, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=50, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.cashfree_order_id} - {self.user.username}"
from django.db import models

# Create your models here.
