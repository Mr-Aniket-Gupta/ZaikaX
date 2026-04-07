from django.urls import path
from . import views

urlpatterns = [
    path('add/<int:item_id>/', views.add_to_cart, name='add_to_cart'),
    path('', views.cart_view, name='cart'),
    path('update/<int:item_id>/<str:action>/', views.update_cart_quantity, name='update_cart_quantity'),
    path('remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('coupon/apply/', views.apply_coupon, name='apply_coupon'),
    path('coupon/remove/', views.remove_coupon, name='remove_coupon'),
    path('checkout/', views.checkout, name='checkout'),
    path('process_order/', views.process_order, name='process_order'),
    path('confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    path('orders/', views.order_history, name='order_history'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
]
