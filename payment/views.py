import json
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from cart.models import CartItem
from .models import PaymentSession
from accounts.models import Address
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from cart.models import Order, OrderItem
from django.core import serializers

@csrf_exempt
def create_cashfree_order(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    user = request.user
    if not user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    # Calculate cart total
    cart_items = CartItem.objects.filter(user=user)
    if not cart_items.exists():
        return JsonResponse({"error": "Cart is empty"}, status=400)

    total_amount = sum(item.total_price() for item in cart_items)

    payload = {
        "order_amount": float(total_amount),
        "order_currency": "INR",
        "customer_details": {
            "customer_id": str(user.id),
            "customer_phone": "9999999999"
        }
    }

    headers = {
        "Content-Type": "application/json",
        "x-api-version": "2025-01-01",
        "x-client-id": settings.CASHFREE_CLIENT_ID,
        "x-client-secret": settings.CASHFREE_CLIENT_SECRET
    }

    response = requests.post(
        "https://sandbox.cashfree.com/pg/orders",
        headers=headers,
        json=payload
    )

    data = response.json()

    if response.status_code != 200:
        return JsonResponse(data, status=500)

    # Save a PaymentSession record linking this cashfree order to our user
    selected_address = None
    try:
        payload = json.loads(request.body)
        sel = payload.get('selected_address')
        if sel and sel != '':
            # if new address fields were provided, create Address
            if sel == 'new':
                addr_form = None
                # build Address from payload fields
                try:
                    addr = Address.objects.create(
                        user=user,
                        full_name=payload.get('full_name',''),
                        email=payload.get('email', user.email),
                        phone=payload.get('phone',''),
                        address_line1=payload.get('address_line1',''),
                        address_line2=payload.get('address_line2',''),
                        city=payload.get('city',''),
                        state=payload.get('state',''),
                        pincode=payload.get('pincode',''),
                        country=payload.get('country',''),
                    )
                    selected_address = addr
                except Exception:
                    selected_address = None
            else:
                try:
                    selected_address = Address.objects.get(id=sel, user=user)
                except Address.DoesNotExist:
                    selected_address = None
    except Exception:
        selected_address = None

    payment = PaymentSession.objects.create(
        user=user,
        cashfree_order_id=data.get('order_id'),
        payment_session_id=data.get('payment_session_id'),
        amount=total_amount,
        address=selected_address,
        status='created'
    )

    return JsonResponse({
        "payment_session_id": data.get("payment_session_id"),
        "order_id": data.get("order_id")
    })


@require_POST
@csrf_exempt
def confirm_payment(request):
    """Endpoint to be called after payment completion to record payment and create Order."""
    payload = json.loads(request.body)
    order_id = payload.get('order_id')
    payment_status = payload.get('status')

    if not order_id:
        return JsonResponse({'error':'order_id required'}, status=400)

    try:
        ps = PaymentSession.objects.get(cashfree_order_id=order_id)
    except PaymentSession.DoesNotExist:
        return JsonResponse({'error':'unknown order'}, status=404)

    # update status
    ps.status = payment_status or 'unknown'
    ps.save()

    if payment_status == 'PAID' or payment_status == 'SUCCESS':
        # create Order and OrderItems from user's cart
        cart_items = CartItem.objects.filter(user=ps.user)
        if not cart_items.exists():
            return JsonResponse({'error':'cart empty'}, status=400)

        total_amount = sum(ci.total_price() for ci in cart_items)

        new_order = Order.objects.create(
            user=ps.user,
            full_name=ps.address.full_name if ps.address else ps.user.username,
            phone=ps.address.phone if ps.address else '',
            address=f"{ps.address.address_line1} {ps.address.address_line2 or ''}, {ps.address.city}" if ps.address else '',
            city=ps.address.city if ps.address else '',
            pincode=ps.address.pincode if ps.address else '',
            total_price=total_amount,
            status=Order.STATUS_PLACED
        )

        for ci in cart_items:
            OrderItem.objects.create(
                order=new_order,
                item=ci.item,
                quantity=ci.quantity,
                price_at_purchase=ci.item.price
            )

        # clear cart
        cart_items.delete()

        return JsonResponse({'status':'order_created','order_id': new_order.id})

    return JsonResponse({'status':'updated'})


