from django.db import models
from django.utils.text import slugify


DEFAULT_CATEGORY_META = {
    "starters": {"name": "Starters", "icon": "🥗", "display_order": 10},
    "main_course": {"name": "Main Course", "icon": "🍛", "display_order": 20},
    "biryani": {"name": "Biryani", "icon": "🍚", "display_order": 30},
    "breads": {"name": "Breads", "icon": "🍞", "display_order": 40},
    "rice": {"name": "Rice & Noodles", "icon": "🍜", "display_order": 50},
    "snacks": {"name": "Snacks", "icon": "🥟", "display_order": 60},
    "beverages": {"name": "Beverages", "icon": "🥤", "display_order": 70},
    "desserts": {"name": "Desserts", "icon": "🍰", "display_order": 80},
    "chinese": {"name": "Chinese", "icon": "🥡", "display_order": 90},
    "south_indian": {"name": "South Indian", "icon": "🥞", "display_order": 100},
    "rolls": {"name": "Rolls", "icon": "🌯", "display_order": 110},
    "fast_food": {"name": "Fast Food", "icon": "🍟", "display_order": 120},
}


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    icon = models.CharField(max_length=10, blank=True, default="🍽")
    display_order = models.PositiveIntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("display_order", "name")
        verbose_name_plural = "Categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class MenuItem(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=7, decimal_places=2)
    category = models.CharField(max_length=50, db_index=True)
    image = models.ImageField(upload_to="menu/", blank=True, null=True)
    is_veg = models.BooleanField(default=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name

    @property
    def category_obj(self):
        return Category.objects.filter(slug=self.category).first()

    @property
    def category_name(self):
        category = self.category_obj
        if category:
            return category.name
        return self.category.replace("_", " ").title()
