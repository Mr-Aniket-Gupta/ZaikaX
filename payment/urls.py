from django.urls import path
from .views import create_cashfree_order, confirm_payment

urlpatterns = [
    path("create-order/", create_cashfree_order, name="cashfree_create_order"),
    path("confirm/", confirm_payment, name="payment_confirm"),
]
