from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from menu.models import MenuItem


class Coupon(models.Model):
    DISCOUNT_PERCENT = "percent"
    DISCOUNT_FIXED = "fixed"
    DISCOUNT_TYPE_CHOICES = [
        (DISCOUNT_PERCENT, "Percentage"),
        (DISCOUNT_FIXED, "Fixed Amount"),
    ]

    code = models.CharField(max_length=30, unique=True)
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES, default=DISCOUNT_PERCENT)
    discount_value = models.DecimalField(max_digits=8, decimal_places=2)
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(null=True, blank=True)
    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    per_user_limit = models.PositiveIntegerField(default=1)
    used_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.code

    @property
    def is_currently_valid(self):
        now = timezone.now()
        if not self.is_active:
            return False
        if self.valid_from and self.valid_from > now:
            return False
        if self.valid_until and self.valid_until < now:
            return False
        if self.usage_limit is not None and self.used_count >= self.usage_limit:
            return False
        return True


class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def total_price(self):
        return self.quantity * self.item.price

    def __str__(self):
        return f"{self.item.name} - {self.quantity}"


class Order(models.Model):
    PAYMENT_METHOD_COD = "COD"
    PAYMENT_METHOD_ONLINE = "ONLINE"
    PAYMENT_METHOD_CHOICES = [
        (PAYMENT_METHOD_COD, "Cash on Delivery"),
        (PAYMENT_METHOD_ONLINE, "Online Payment"),
    ]

    PAYMENT_PENDING = "Pending"
    PAYMENT_PAID = "Paid"
    PAYMENT_FAILED = "Failed"
    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_PENDING, "Pending"),
        (PAYMENT_PAID, "Paid"),
        (PAYMENT_FAILED, "Failed"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    applied_coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)

    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    city = models.CharField(max_length=50)
    pincode = models.CharField(max_length=10)
    instructions = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    STATUS_PENDING = "Pending"
    STATUS_PLACED = "Placed"
    STATUS_PROCESSING = "Processing"
    STATUS_SHIPPED = "Shipped"
    STATUS_DELIVERED = "Delivered"
    STATUS_CANCELLED = "Cancelled"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PLACED, "Placed"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_SHIPPED, "Shipped"),
        (STATUS_DELIVERED, "Delivered"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    subtotal_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    coupon_code = models.CharField(max_length=30, blank=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default=PAYMENT_METHOD_COD)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default=PAYMENT_PENDING)

    def __str__(self):
        return f"Order {self.id} - {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)

    def get_total_price(self):
        return self.price_at_purchase * self.quantity

    def __str__(self):
        return f"{self.item.name} ({self.quantity})"
