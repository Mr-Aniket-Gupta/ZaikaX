from django.contrib import admin
from .models import FAQ, Review


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question", "created", "updated")
    search_fields = ("question", "answer", "keywords")
    list_filter = ("created",)
    ordering = ("-created",)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("name", "rating", "created")
    list_filter = ("rating", "created")
    search_fields = ("name", "text")
    ordering = ("-created",)
