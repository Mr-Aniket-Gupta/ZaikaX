"""
Seed script to add realistic multi-user sample order data to the database.
This powers admin analytics and user-side recommendations.
"""

from datetime import datetime, time, timedelta
import os
import random
import sys
from pathlib import Path

import django

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ZaikaX.settings")
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone

from cart.models import Order, OrderItem
from menu.models import MenuItem
from accounts.models import Address


STATUS_CYCLE = [
    Order.STATUS_PENDING,
    Order.STATUS_PLACED,
    Order.STATUS_PROCESSING,
    Order.STATUS_SHIPPED,
    Order.STATUS_DELIVERED,
    Order.STATUS_CANCELLED,
]

CITY_DEMAND_PATTERNS = {
    "Delhi": {"keywords": ["Chicken", "Butter", "Naan", "Tandoori"], "weekend_boost": 1.45},
    "Mumbai": {"keywords": ["Paneer", "Roll", "Sandwich", "Fries"], "weekend_boost": 1.35},
    "Ahmedabad": {"keywords": ["Veg", "Paneer", "Manchurian", "Rice"], "weekend_boost": 1.2},
    "Chandigarh": {"keywords": ["Chicken", "Tandoori", "Biryani", "Lassi"], "weekend_boost": 1.4},
    "Bengaluru": {"keywords": ["Dosa", "Idli", "Rice", "Coffee"], "weekend_boost": 1.3},
    "Lucknow": {"keywords": ["Biryani", "Kabab", "Chicken", "Kulfi"], "weekend_boost": 1.5},
}

USER_PERSONAS = {
    "rahul_foodie": {
        "label": "North Indian Feast Lover",
        "keywords": ["Butter Chicken", "Chicken Biryani", "Butter Naan", "Chicken Tandoori"],
    },
    "neha_cravings": {
        "label": "Snack And Quick Bites",
        "keywords": ["Paneer", "Roll", "Sandwich", "Fries", "Cold Coffee"],
    },
    "arjun_spice": {
        "label": "Veg Indo-Chinese Fan",
        "keywords": ["Paneer", "Veg", "Manchurian", "Fried Rice", "Noodles"],
    },
    "simran_bites": {
        "label": "Grill And Tandoor Favorite",
        "keywords": ["Chicken", "Tandoori", "Butter Chicken", "Lassi"],
    },
    "kiran_combo": {
        "label": "South Indian Comfort Picks",
        "keywords": ["Dosa", "Idli", "Rice", "Chai"],
    },
    "aisha_flavors": {
        "label": "Biryani And Mughlai Cravings",
        "keywords": ["Biryani", "Kabab", "Chicken", "Mutton", "Kulfi"],
    },
}

DEFAULT_COMBOS = [
    ["Chicken", "Biryani", "Lassi"],
    ["Paneer", "Naan", "Dal"],
    ["Tandoori", "Butter Chicken", "Butter Naan"],
    ["Fried Rice", "Manchurian"],
    ["Sandwich", "Fries", "Lassi"],
    ["Dosa", "Idli", "Masala Chai"],
]


def _pick_items(menu_items, keywords):
    selected = []
    for keyword in keywords:
        match = next((item for item in menu_items if keyword.lower() in item.name.lower()), None)
        if match and match not in selected:
            selected.append(match)
    return selected


def _default_address_for(user):
    return user.addresses.filter(is_default=True).first() or user.addresses.first()


def _weighted_matches(menu_items, keywords):
    selected = []
    for keyword in keywords:
        keyword_lower = keyword.lower()
        matches = [item for item in menu_items if keyword_lower in item.name.lower()]
        if matches:
            for match in matches:
                if match not in selected:
                    selected.append(match)
                    break
    return selected


def _build_persona_combo_pool(menu_items, user, address):
    persona = USER_PERSONAS.get(user.username, {})
    city_pattern = CITY_DEMAND_PATTERNS.get(address.city, {})

    persona_items = _weighted_matches(menu_items, persona.get("keywords", []))
    city_items = _weighted_matches(menu_items, city_pattern.get("keywords", []))

    combos = []
    if persona_items:
        combos.append(persona_items[: min(4, len(persona_items))])
    if city_items:
        combos.append(city_items[: min(4, len(city_items))])

    for default_keywords in DEFAULT_COMBOS:
        default_items = _pick_items(menu_items, default_keywords)
        if default_items:
            combos.append(default_items)

    return [combo for combo in combos if combo]


def _planned_order_time(now, index, city):
    day_offset = random.randint(0, 89)
    target_date = (now - timedelta(days=day_offset)).date()

    city_boost = CITY_DEMAND_PATTERNS.get(city, {}).get("weekend_boost", 1.0)
    weekend_probability = min(0.35 * city_boost, 0.85)
    if random.random() < weekend_probability:
        days_back = (target_date.weekday() - 5) % 7
        target_date = target_date - timedelta(days=days_back)

    if target_date.weekday() >= 5:
        hour = random.choice([12, 13, 14, 19, 20, 21, 22])
    else:
        hour = random.choice([11, 13, 14, 18, 19, 20])

    minute = random.choice([0, 10, 15, 20, 30, 40, 45, 50])
    second = random.randint(0, 50)
    naive_dt = datetime.combine(target_date, time(hour=hour, minute=minute, second=second))
    return timezone.make_aware(naive_dt, timezone.get_current_timezone())


def create_sample_orders():
    """Create realistic sample orders with repeat combos across multiple users."""
    menu_items = list(MenuItem.objects.all())
    if not menu_items:
        print("No menu items found. Please run seed_menu.py first.")
        return

    users = list(User.objects.exclude(is_staff=True).order_by("id"))
    if not users:
        print("No non-admin users found. Please run seed_users.py first.")
        return

    missing_addresses = [user.username for user in users if not _default_address_for(user)]
    if missing_addresses:
        print("Some users do not have addresses. Please run seed_users.py again.")
        print("Missing address for:", ", ".join(missing_addresses))
        return

    # Keep the sample dataset repeatable across reruns.
    OrderItem.objects.all().delete()
    Order.objects.filter(user__in=users).delete()

    orders_created = []
    random.seed(42)

    total_target_orders = max(36, len(users) * 8)
    weekend_orders = 0
    city_summary = {city: 0 for city in CITY_DEMAND_PATTERNS.keys()}
    persona_summary = {}

    for i in range(total_target_orders):
        user = users[i % len(users)]
        address = _default_address_for(user)
        order_time = _planned_order_time(timezone.now(), i, address.city)
        status = STATUS_CYCLE[i % len(STATUS_CYCLE)]

        combo_pool = _build_persona_combo_pool(menu_items, user, address)
        combo = combo_pool[i % len(combo_pool)] if combo_pool else random.sample(menu_items, min(3, len(menu_items)))
        selected_items = list(combo)

        if order_time.weekday() >= 5:
            weekend_orders += 1
            if len(menu_items) > len(selected_items):
                extra_weekend_pool = [item for item in menu_items if item not in selected_items]
                selected_items.extend(random.sample(extra_weekend_pool, min(random.randint(1, 2), len(extra_weekend_pool))))

        if len(menu_items) > len(selected_items) and random.random() > 0.45:
            extra_pool = [item for item in menu_items if item not in selected_items]
            selected_items.extend(random.sample(extra_pool, min(random.randint(0, 2), len(extra_pool))))

        city_summary[address.city] = city_summary.get(address.city, 0) + 1
        persona_label = USER_PERSONAS.get(user.username, {}).get("label", "General Customer")
        persona_summary[persona_label] = persona_summary.get(persona_label, 0) + 1

        order = Order.objects.create(
            user=user,
            full_name=address.full_name,
            address=f"{address.address_line1} {address.address_line2 or ''}".strip(),
            city=address.city,
            pincode=address.pincode,
            phone=address.phone,
            status=status,
            instructions=f"Seeded order #{i + 1} for analytics and recommendations",
        )

        # Backdate orders so dashboard charts have spread-out sample activity.
        Order.objects.filter(pk=order.pk).update(created_at=order_time, updated_at=order_time)
        order.refresh_from_db()
        total_order_price = 0

        for menu_item in selected_items:
            quantity = random.randint(1, 3)
            OrderItem.objects.create(
                order=order,
                item=menu_item,
                quantity=quantity,
                price_at_purchase=menu_item.price,
            )
            total_order_price += menu_item.price * quantity

        order.total_price = total_order_price
        order.save(update_fields=["total_price", "updated_at"])

        orders_created.append(order)
        print(
            f"Created order {i + 1}/{total_target_orders}: "
            f"User={user.username}, City={address.city}, Persona={persona_label}, "
            f"Status={status}, Date={order_time.date()}, Items={len(selected_items)}"
        )

    print("\nSummary:")
    print(f"   Total orders created: {len(orders_created)}")
    print(f"   Pending: {Order.objects.filter(status=Order.STATUS_PENDING).count()}")
    print(f"   Delivered: {Order.objects.filter(status=Order.STATUS_DELIVERED).count()}")
    print(f"   Cancelled: {Order.objects.filter(status=Order.STATUS_CANCELLED).count()}")
    print(f"   Order items created: {OrderItem.objects.count()}")
    print(f"   Total users: {User.objects.count()}")
    print(f"   Weekend orders: {weekend_orders}")

    print("\nCity demand pattern:")
    for city, count in sorted(city_summary.items(), key=lambda item: (-item[1], item[0])):
        print(f"   {city}: {count} orders")

    print("\nCustomer personas:")
    for persona, count in sorted(persona_summary.items(), key=lambda item: (-item[1], item[0])):
        print(f"   {persona}: {count} orders")

    print("\nSample data loaded! Your admin dashboard should now show data.")


if __name__ == "__main__":
    create_sample_orders()
