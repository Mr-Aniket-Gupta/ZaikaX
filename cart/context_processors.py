from .models import CartItem


def cart_count(request):
    """Add cart item count (sum of quantities) for authenticated users."""
    if request.user.is_authenticated:
        try:
            qs = CartItem.objects.filter(user=request.user)
            total = sum(ci.quantity for ci in qs)
        except Exception:
            total = 0
        return {'cart_count': total}
    return {'cart_count': 0}
