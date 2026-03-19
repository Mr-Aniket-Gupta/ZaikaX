from django.contrib import admin
from .models import CartItem, Order, OrderItem


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
	list_display = ('user', 'item', 'quantity')
	search_fields = ('user__username', 'item__name')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
	list_display = ('id', 'user', 'full_name', 'phone', 'city', 'pincode', 'total_price', 'created_at', 'status')
	list_filter = ('status', 'created_at')
	search_fields = ('user__username', 'full_name', 'phone')


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
	list_display = ('order', 'item', 'quantity', 'price_at_purchase')
	search_fields = ('order__id', 'item__name')