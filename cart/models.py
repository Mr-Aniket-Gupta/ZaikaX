from django.db import models
from django.contrib.auth.models import User
from menu.models import MenuItem



class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def total_price(self):
        return self.quantity * self.item.price

    def __str__(self):
        return f"{self.item.name} - {self.quantity}"
    

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # Delivery details
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    city = models.CharField(max_length=50)
    pincode = models.CharField(max_length=10)
    instructions = models.TextField(blank=True, null=True)

    # Order metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    STATUS_PENDING = 'Pending'
    STATUS_PLACED = 'Placed'
    STATUS_PROCESSING = 'Processing'
    STATUS_SHIPPED = 'Shipped'
    STATUS_DELIVERED = 'Delivered'
    STATUS_CANCELLED = 'Cancelled'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PLACED, 'Placed'),
        (STATUS_PROCESSING, 'Processing'),
        (STATUS_SHIPPED, 'Shipped'),
        (STATUS_DELIVERED, 'Delivered'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)

    # Financial
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Order {self.id} - {self.user.username}"



class OrderItem(models.Model):
    # Links to the specific order this item belongs to
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    
    # Links to the menu item that was purchased
    item = models.ForeignKey(MenuItem, on_delete=models.CASCADE) 
    
    # Details at the time of purchase
    quantity = models.IntegerField(default=1)
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2) 
    
    def get_total_price(self):
        return self.price_at_purchase * self.quantity

    def __str__(self):
        return f"{self.item.name} ({self.quantity})"
