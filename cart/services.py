from decimal import Decimal

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from accounts.forms import AddressForm
from accounts.models import Address

from .models import CartItem, Coupon, Order, OrderItem


FREE_DELIVERY_THRESHOLD = Decimal("499.00")
STANDARD_DELIVERY_FEE = Decimal("40.00")
COUPON_SESSION_KEY = "applied_coupon_code"


def get_active_coupons():
    now = timezone.now()
    return Coupon.objects.filter(is_active=True, valid_from__lte=now).filter(
        valid_until__isnull=True
    ) | Coupon.objects.filter(is_active=True, valid_from__lte=now, valid_until__gte=now)


def get_coupon_from_session(request):
    code = request.session.get(COUPON_SESSION_KEY)
    if not code:
        return None
    return Coupon.objects.filter(code__iexact=code).first()


def set_coupon_in_session(request, coupon):
    request.session[COUPON_SESSION_KEY] = coupon.code
    request.session.modified = True


def clear_coupon_session(request):
    if COUPON_SESSION_KEY in request.session:
        del request.session[COUPON_SESSION_KEY]
        request.session.modified = True


def get_cart_items_for_user(user):
    return CartItem.objects.filter(user=user).select_related("item")


def validate_coupon_for_user(coupon, user, subtotal):
    if not coupon:
        return False, "Coupon not found."
    if not coupon.is_currently_valid:
        return False, "This coupon is not active right now."
    if Decimal(subtotal) < coupon.min_order_amount:
        return False, f"Minimum order amount for this coupon is Rs {coupon.min_order_amount}."

    user_usage = Order.objects.filter(user=user, applied_coupon=coupon).count()
    if coupon.per_user_limit and user_usage >= coupon.per_user_limit:
        return False, "You have already used this coupon the maximum number of times."

    return True, ""


def calculate_discount(coupon, subtotal):
    subtotal = Decimal(subtotal or 0)
    if not coupon:
        return Decimal("0.00")

    if coupon.discount_type == Coupon.DISCOUNT_PERCENT:
        discount = (subtotal * Decimal(coupon.discount_value)) / Decimal("100")
    else:
        discount = Decimal(coupon.discount_value)

    if coupon.max_discount_amount:
        discount = min(discount, Decimal(coupon.max_discount_amount))

    return min(discount, subtotal)


def build_cart_pricing(user, coupon=None):
    items = list(get_cart_items_for_user(user))
    subtotal = sum((item.total_price() for item in items), Decimal("0.00"))
    delivery_fee = Decimal("0.00") if subtotal >= FREE_DELIVERY_THRESHOLD else STANDARD_DELIVERY_FEE

    valid_coupon = None
    discount_amount = Decimal("0.00")
    coupon_error = ""
    if coupon:
        is_valid, coupon_error = validate_coupon_for_user(coupon, user, subtotal)
        if is_valid:
            valid_coupon = coupon
            discount_amount = calculate_discount(coupon, subtotal)

    total = max(subtotal + delivery_fee - discount_amount, Decimal("0.00"))

    return {
        "items": items,
        "subtotal": subtotal,
        "delivery_fee": delivery_fee,
        "discount_amount": discount_amount,
        "total": total,
        "coupon": valid_coupon,
        "coupon_error": coupon_error,
    }


def resolve_delivery_address(request, user):
    selected_address_id = request.POST.get("selected_address")
    delivery_address = None

    if selected_address_id and selected_address_id != "new":
        delivery_address = Address.objects.filter(id=selected_address_id, user=user).first()

    if selected_address_id == "new":
        form = AddressForm(request.POST)
        if form.is_valid():
            delivery_address = form.save(commit=False)
            delivery_address.user = user
            delivery_address.save()
        else:
            return None, form

    return delivery_address, None


@transaction.atomic
def create_order_from_cart(
    user,
    delivery_address,
    instructions="",
    payment_method=Order.PAYMENT_METHOD_COD,
    payment_status=Order.PAYMENT_PENDING,
    coupon=None,
):
    pricing = build_cart_pricing(user, coupon=coupon)
    cart_items = pricing["items"]
    if not cart_items:
        raise ValueError("Cart is empty.")

    if coupon and not pricing["coupon"]:
        raise ValueError(pricing["coupon_error"] or "Invalid coupon.")

    order_status = Order.STATUS_PLACED if payment_method == Order.PAYMENT_METHOD_ONLINE else Order.STATUS_PENDING

    order = Order.objects.create(
        user=user,
        applied_coupon=pricing["coupon"],
        full_name=delivery_address.full_name if delivery_address else user.username,
        phone=delivery_address.phone if delivery_address else "",
        address=f"{delivery_address.address_line1} {delivery_address.address_line2 or ''}, {delivery_address.city}" if delivery_address else "",
        city=delivery_address.city if delivery_address else "",
        pincode=delivery_address.pincode if delivery_address else "",
        instructions=instructions,
        subtotal_price=pricing["subtotal"],
        delivery_fee=pricing["delivery_fee"],
        discount_amount=pricing["discount_amount"],
        total_price=pricing["total"],
        coupon_code=pricing["coupon"].code if pricing["coupon"] else "",
        payment_method=payment_method,
        payment_status=payment_status,
        status=order_status,
    )

    for cart_item in cart_items:
        OrderItem.objects.create(
            order=order,
            item=cart_item.item,
            quantity=cart_item.quantity,
            price_at_purchase=cart_item.item.price,
        )

    if pricing["coupon"]:
        Coupon.objects.filter(id=pricing["coupon"].id).update(used_count=F("used_count") + 1)

    CartItem.objects.filter(id__in=[item.id for item in cart_items]).delete()
    return order, pricing
