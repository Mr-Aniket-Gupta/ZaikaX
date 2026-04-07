import json

import requests
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from accounts.models import Address
from cart.models import Order
from cart.services import (
    build_cart_pricing,
    clear_coupon_session,
    create_order_from_cart,
    get_coupon_from_session,
)
from .models import PaymentSession


@csrf_exempt
def create_cashfree_order(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    user = request.user
    if not user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    coupon = get_coupon_from_session(request)
    pricing = build_cart_pricing(user, coupon=coupon)
    cart_items = pricing["items"]
    if not cart_items:
        return JsonResponse({"error": "Cart is empty"}, status=400)

    payload = {
        "order_amount": float(pricing["total"]),
        "order_currency": "INR",
        "customer_details": {
            "customer_id": str(user.id),
            "customer_phone": "9999999999",
        },
    }

    headers = {
        "Content-Type": "application/json",
        "x-api-version": "2025-01-01",
        "x-client-id": settings.CASHFREE_CLIENT_ID,
        "x-client-secret": settings.CASHFREE_CLIENT_SECRET,
    }

    response = requests.post("https://sandbox.cashfree.com/pg/orders", headers=headers, json=payload)
    data = response.json()

    if response.status_code != 200:
        return JsonResponse(data, status=500)

    selected_address = None
    try:
        body = json.loads(request.body)
        selected_id = body.get("selected_address")
        if selected_id and selected_id != "new":
            selected_address = Address.objects.filter(id=selected_id, user=user).first()
    except Exception:
        selected_address = None

    PaymentSession.objects.create(
        user=user,
        cashfree_order_id=data.get("order_id"),
        payment_session_id=data.get("payment_session_id"),
        amount=pricing["total"],
        address=selected_address,
        status="created",
    )

    return JsonResponse(
        {
            "payment_session_id": data.get("payment_session_id"),
            "order_id": data.get("order_id"),
        }
    )


@require_POST
@csrf_exempt
def confirm_payment(request):
    payload = json.loads(request.body)
    order_id = payload.get("order_id")
    payment_status = payload.get("status")

    if not order_id:
        return JsonResponse({"error": "order_id required"}, status=400)

    try:
        payment_session = PaymentSession.objects.get(cashfree_order_id=order_id)
    except PaymentSession.DoesNotExist:
        return JsonResponse({"error": "unknown order"}, status=404)

    payment_session.status = payment_status or "unknown"
    payment_session.save()

    if payment_status in {"PAID", "SUCCESS"}:
        coupon = get_coupon_from_session(request)
        try:
            order, _pricing = create_order_from_cart(
                payment_session.user,
                payment_session.address,
                payment_method=Order.PAYMENT_METHOD_ONLINE,
                payment_status=Order.PAYMENT_PAID,
                coupon=coupon,
            )
        except ValueError as exc:
            return JsonResponse({"error": str(exc)}, status=400)

        clear_coupon_session(request)
        return JsonResponse({"status": "order_created", "order_id": order.id})

    return JsonResponse({"status": "updated"})
