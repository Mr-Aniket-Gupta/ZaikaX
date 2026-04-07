from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.forms import AddressForm
from accounts.models import Address
from menu.models import MenuItem
from main.recommendations import get_frequently_bought_together, get_personalized_recommendations

from .models import CartItem, Coupon, Order
from .services import (
    build_cart_pricing,
    clear_coupon_session,
    create_order_from_cart,
    get_active_coupons,
    get_coupon_from_session,
    resolve_delivery_address,
    set_coupon_in_session,
)


@login_required(login_url="login")
def add_to_cart(request, item_id):
    item = get_object_or_404(MenuItem, id=item_id)
    cart_item, created = CartItem.objects.get_or_create(user=request.user, item=item)

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    messages.success(request, f"{item.name} added to cart!")
    return redirect("cart")


@login_required(login_url="login")
def cart_view(request):
    applied_coupon = get_coupon_from_session(request)
    pricing = build_cart_pricing(request.user, coupon=applied_coupon)
    if applied_coupon and not pricing["coupon"]:
        clear_coupon_session(request)
        applied_coupon = None
        pricing = build_cart_pricing(request.user, coupon=None)

    return render(
        request,
        "cart/cart.html",
        {
            "items": pricing["items"],
            "total": pricing["total"],
            "subtotal": pricing["subtotal"],
            "delivery_fee": pricing["delivery_fee"],
            "discount_amount": pricing["discount_amount"],
            "applied_coupon": pricing["coupon"],
            "available_coupons": get_active_coupons().distinct()[:4],
            "recommendations": get_personalized_recommendations(request.user, cart_items=pricing["items"], limit=4),
            "frequently_bought_together": get_frequently_bought_together(cart_items=pricing["items"], limit=3),
        },
    )


@require_POST
@login_required(login_url="login")
def apply_coupon(request):
    code = (request.POST.get("coupon_code") or "").strip()
    redirect_to = request.POST.get("next") or "checkout"
    coupon = Coupon.objects.filter(code__iexact=code).first()
    pricing = build_cart_pricing(request.user, coupon=coupon)

    if not code:
        messages.error(request, "Please enter a coupon code.")
    elif pricing["coupon"]:
        set_coupon_in_session(request, pricing["coupon"])
        messages.success(request, f"Coupon {pricing['coupon'].code} applied successfully.")
    else:
        clear_coupon_session(request)
        messages.error(request, pricing["coupon_error"] or "Coupon could not be applied.")

    return redirect(redirect_to)


@require_POST
@login_required(login_url="login")
def remove_coupon(request):
    clear_coupon_session(request)
    messages.info(request, "Coupon removed from your order.")
    return redirect(request.POST.get("next") or "checkout")


@require_POST
@login_required(login_url="login")
def remove_from_cart(request, item_id):
    try:
        cart_item = CartItem.objects.get(user=request.user, item__id=item_id)
        item_name = cart_item.item.name
        cart_item.delete()
        messages.success(request, f"Removed {item_name} from your cart.")
    except CartItem.DoesNotExist:
        messages.error(request, "That item was not found in your cart.")

    return redirect("cart")


@login_required(login_url="login")
def update_cart_quantity(request, item_id, action):
    if request.method != "POST":
        return redirect("cart")

    cart_item = get_object_or_404(CartItem, user=request.user, item__id=item_id)

    if action == "inc":
        cart_item.quantity += 1
        cart_item.save()
    elif action == "dec":
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
            messages.info(request, f"{cart_item.item.name} removed from your cart.")

    return redirect("cart")


@login_required(login_url="login")
def checkout(request):
    applied_coupon = get_coupon_from_session(request)
    pricing = build_cart_pricing(request.user, coupon=applied_coupon)
    items = pricing["items"]
    if not items:
        messages.error(request, "Your cart is empty. Please add items before checking out.")
        return redirect("cart")

    addresses = Address.objects.filter(user=request.user)
    default_addr = addresses.filter(is_default=True).first()
    default_address_id = default_addr.id if default_addr else (addresses.first().id if addresses.exists() else None)

    return render(
        request,
        "cart/checkout.html",
        {
            "items": items,
            "subtotal": pricing["subtotal"],
            "delivery_fee": pricing["delivery_fee"],
            "discount_amount": pricing["discount_amount"],
            "total": pricing["total"],
            "applied_coupon": pricing["coupon"],
            "available_coupons": get_active_coupons().distinct()[:6],
            "addresses": addresses,
            "address_form": AddressForm(),
            "default_address_id": default_address_id,
        },
    )


@login_required(login_url="login")
def process_order(request):
    if request.method != "POST":
        return redirect("checkout")

    pricing = build_cart_pricing(request.user, coupon=get_coupon_from_session(request))
    if not pricing["items"]:
        messages.error(request, "Your cart is empty.")
        return redirect("cart")

    delivery_address, form = resolve_delivery_address(request, request.user)
    if form is not None:
        messages.error(request, "Please correct the address errors and try again.")
        return redirect("checkout")

    if not delivery_address:
        messages.error(request, "Please select or add a delivery address.")
        return redirect("checkout")

    payment_method = request.POST.get("payment_method") or Order.PAYMENT_METHOD_COD
    if payment_method != Order.PAYMENT_METHOD_COD:
        messages.info(request, "Online payment checkout will be enabled through the payment flow. Please use Cash on Delivery for now.")
        return redirect("checkout")
    applied_coupon = get_coupon_from_session(request)

    try:
        order, _pricing = create_order_from_cart(
            request.user,
            delivery_address,
            instructions=request.POST.get("instructions", ""),
            payment_method=payment_method,
            payment_status=Order.PAYMENT_PENDING,
            coupon=applied_coupon,
        )
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect("checkout")

    clear_coupon_session(request)
    messages.success(request, "Order placed successfully.")
    return redirect("order_confirmation", order_id=order.id)


@login_required(login_url="login")
def order_confirmation(request, order_id):
    order = get_object_or_404(Order.objects.prefetch_related("items__item"), id=order_id, user=request.user)
    return render(request, "cart/order_confirmation.html", {"order": order})


@login_required(login_url="login")
def order_history(request):
    orders = Order.objects.filter(user=request.user).prefetch_related("items__item").order_by("-created_at")
    return render(request, "cart/order_history.html", {"orders": orders})


@login_required(login_url="login")
def order_detail(request, order_id):
    order = get_object_or_404(Order.objects.prefetch_related("items__item"), id=order_id, user=request.user)
    return render(request, "cart/order_detail.html", {"order": order})
