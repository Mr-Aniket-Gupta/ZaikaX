"""
Seed script to add sample order data to the database
This helps populate the admin dashboard with real data for testing
"""

from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from cart.models import Order, OrderItem, MenuItem
import random


def create_sample_orders():
    """Create sample orders with various statuses and items"""
    
    # Get or create a test user
    user, created = User.objects.get_or_create(
        username='testcustomer',
        defaults={
            'email': 'testcustomer@example.com',
            'first_name': 'Test',
            'last_name': 'Customer'
        }
    )
    
    # Get all menu items
    menu_items = MenuItem.objects.all()
    
    if not menu_items.exists():
        print("❌ No menu items found! Please run seed_menu.py first.")
        return
    
    # Status choices
    # Status choices
    status_choices = ['Pending', 'Placed', 'Processing', 'Shipped', 'Delivered', 'Cancelled']
    
    # Create 15 sample orders
    orders_created = []
    
    for i in range(15):
    
        for i in range(15):
            # Vary the order dates
            days_ago = random.randint(0, 30)
            order_time = timezone.now() - timedelta(days=days_ago)
            
            status = random.choice(status_choices)
            
            # Create order with only valid fields
            order = Order.objects.create(
                user=user,
                full_name=f"Test Customer {i+1}",
                address=f"{random.randint(1, 500)} {random.choice(['Main', 'Oak', 'Elm', 'Park'])} Street",
                city=random.choice(['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix']),
                pincode=f"{random.randint(10000, 99999)}",
                phone="555-0100",
                status=status,
                instructions=f"Order {i+1}: Please handle with care"
            )
        
            # Add 1-4 random items to each order
            num_items = random.randint(1, 4)
            selected_items = random.sample(list(menu_items), min(num_items, len(menu_items)))
            
            total_order_price = 0
            for menu_item in selected_items:
                quantity = random.randint(1, 3)
                price_at_purchase = menu_item.price
                OrderItem.objects.create(
                    order=order,
                    item=menu_item,
                    quantity=quantity,
                    price_at_purchase=price_at_purchase
                )
                total_order_price += price_at_purchase * quantity
            
            # Update the order's total_price
            order.total_price = total_order_price
            order.save()
            
            orders_created.append(order)
            print(f"✅ Created order {i+1}/15: Status={status}, Date={order_time.date()}, Items={len(selected_items)}")
    
    print(f"\n📊 Summary:")
    print(f"   Total orders created: {len(orders_created)}")
    print(f"   Pending: {Order.objects.filter(status='Pending').count()}")
    print(f"   Delivered: {Order.objects.filter(status='Delivered').count()}")
    print(f"   Cancelled: {Order.objects.filter(status='Cancelled').count()}")
    print(f"   Total users: {User.objects.count()}")
    print(f"\n✨ Sample data loaded! Your admin dashboard should now show data.")


if __name__ == '__main__':
    create_sample_orders()
