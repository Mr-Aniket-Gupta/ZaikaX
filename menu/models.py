from django.db import models

class MenuItem(models.Model):
    CATEGORY_CHOICES = [
        ('starters', 'Starters'),
        ('main_course', 'Main Course'),
        ('biryani', 'Biryani'),
        ('breads', 'Breads'),
        ('rice', 'Rice & Noodles'),
        ('snacks', 'Snacks'),
        ('beverages', 'Beverages'),
        ('desserts', 'Desserts'),
    ]

    name = models.CharField(max_length=200, unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=7, decimal_places=2)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    image = models.ImageField(upload_to='menu/', blank=True, null=True)
    is_veg = models.BooleanField(default=True)

    def __str__(self):
        return self.name
