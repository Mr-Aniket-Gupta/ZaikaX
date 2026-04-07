from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from menu.models import MenuItem
from .models import CartItem, Order, OrderItem
from django.db import transaction # Important for database integrity
from accounts.models import Address
from accounts.forms import AddressForm
from main.recommendations import get_frequently_bought_together, get_personalized_recommendations


# ➤ Add item to cart
@login_required(login_url='login')
def add_to_cart(request, item_id):
    """Add a menu item to the user's cart."""
    item = get_object_or_404(MenuItem, id=item_id)

    # Check if already in cart
    cart_item, created = CartItem.objects.get_or_create(
        user=request.user,
        item=item
    )

    if not created:
        cart_item.quantity += 1  # increase quantity
        cart_item.save()

    messages.success(request, f"{item.name} added to cart!")
    return redirect('cart')  # show the cart after adding


# ➤ View cart
def cart_view(request):
    """Display the cart page. If user is not logged in, show message + redirect."""
    if not request.user.is_authenticated:
        messages.warning(request, "Please login first to view your cart.")
        return redirect('login')

    items = CartItem.objects.filter(user=request.user)
    total = sum(i.total_price() for i in items)

    return render(request, "cart/cart.html", {
        "items": items,
        "total": total,
        "recommendations": get_personalized_recommendations(request.user, cart_items=items, limit=4),
        "frequently_bought_together": get_frequently_bought_together(cart_items=items, limit=3),
    })

def remove_from_cart(request, item_id):
    """Removes a CartItem entirely from the cart."""
    if request.method == 'POST':
        # Find the specific CartItem for the logged-in user and the menu item ID
        try:
            cart_item = CartItem.objects.get(user=request.user, item__id=item_id)
            item_name = cart_item.item.name # Get the name before deleting
            
            # Delete the item
            cart_item.delete()
            messages.success(request, f"Removed {item_name} from your cart.")
            
        except CartItem.DoesNotExist:
            messages.error(request, "That item was not found in your cart.")
            
        return redirect('cart') # Redirect back to the cart view
    
    # If accessed via GET (e.g., typing the URL), redirect to cart view
    return redirect('cart')


@login_required(login_url='login')
def update_cart_quantity(request, item_id, action):
    """Increase or decrease a cart item's quantity."""
    if request.method != 'POST':
        return redirect('cart')

    cart_item = get_object_or_404(CartItem, user=request.user, item__id=item_id)

    if action == 'inc':
        cart_item.quantity += 1
        cart_item.save()
    elif action == 'dec':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
            messages.info(request, f"{cart_item.item.name} removed from your cart.")

    return redirect('cart')

def checkout(request):
    """
    Displays the final order summary before payment/confirmation.
    """
    # 1. Get all items for the currently logged-in user
    items = CartItem.objects.filter(user=request.user)
    
    # 2. Handle empty cart scenario
    if not items:
        messages.error(request, "Your cart is empty. Please add items before checking out.")
        return redirect('cart')

    # 3. Calculate the total price
    total = sum(i.total_price() for i in items)
    
    addresses = []
    address_form = None
    if request.user.is_authenticated:
        addresses = Address.objects.filter(user=request.user)
        # prefer default address first
        default_addr = addresses.filter(is_default=True).first()
        default_address_id = default_addr.id if default_addr else (addresses.first().id if addresses.exists() else None)
        address_form = AddressForm()

    context = {
        "items": items,
        "total": total,
        "addresses": addresses,
        "address_form": address_form,
        "default_address_id": default_address_id,
    }
    
    return render(request, 'cart/checkout.html', context)

@login_required(login_url='login')
@transaction.atomic # Ensures that all database operations succeed or fail together
def process_order(request):
    """
    Handles final order submission, converts CartItems to OrderItems,
    and clears the cart.
    """
    if request.method == 'POST':
        # 1. Get cart items and total (reusing logic from checkout)
        cart_items = CartItem.objects.filter(user=request.user)
        total_amount = sum(item.total_price() for item in cart_items)

        if not cart_items:
            messages.error(request, "Your cart is empty.")
            return redirect('cart')

        # Determine delivery address: existing or new
        selected_address_id = request.POST.get('selected_address')
        delivery_address = None

        # If user selected an existing address id
        if selected_address_id and selected_address_id != 'new':
            try:
                delivery_address = Address.objects.get(id=selected_address_id, user=request.user)
            except Address.DoesNotExist:
                delivery_address = None

        # If user chose to add a new address (select value 'new'), build from POST
        if selected_address_id == 'new':
            form = AddressForm(request.POST)
            if form.is_valid():
                delivery_address = form.save(commit=False)
                delivery_address.user = request.user
                delivery_address.save()
            else:
                # address validation failed; send user back to checkout with error
                messages.error(request, 'Please correct the address errors and try again.')
                return redirect('checkout')

        # 2. Create the main Order object
        new_order = Order.objects.create(
            user=request.user,
            full_name=delivery_address.full_name if delivery_address else '',
            phone=delivery_address.phone if delivery_address else '',
            address= f"{delivery_address.address_line1} {delivery_address.address_line2 or ''}, {delivery_address.city}" if delivery_address else '',
            city=delivery_address.city if delivery_address else '',
            pincode=delivery_address.pincode if delivery_address else '',
            total_price=total_amount,
        )

        # 3. Transfer items from CartItem to OrderItem for future analytics and recommendations
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=new_order,
                item=cart_item.item,
                quantity=cart_item.quantity,
                price_at_purchase=cart_item.item.price
            )
        
        # 4. Clear the user's cart
        cart_items.delete()

        # 5. Success message and redirect
        messages.success(request, "Order placed successfully! Redirecting to confirmation...")
        
        # For now, we'll redirect to a generic confirmation page.
        return redirect('order_confirmation') 

    # If accessed via GET request, redirect to checkout
    return redirect('checkout')


def order_confirmation(request):
    """Shows the user that their order has been placed."""
    return render(request, 'cart/order_confirmation.html')
