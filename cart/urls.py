from django.urls import path
from . import views

urlpatterns = [
    path('add/<int:item_id>/', views.add_to_cart, name='add_to_cart'),
    path('', views.cart_view, name='cart'),
    path('update/<int:item_id>/<str:action>/', views.update_cart_quantity, name='update_cart_quantity'),
    path('remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('process_order/', views.process_order, name='process_order'),
    path('confirmation/', views.order_confirmation, name='order_confirmation'),
]