from django.db.models import Count, Sum

from cart.models import Order, OrderItem
from menu.models import MenuItem


VALID_RECOMMENDATION_STATUSES = [
    Order.STATUS_PLACED,
    Order.STATUS_PROCESSING,
    Order.STATUS_SHIPPED,
    Order.STATUS_DELIVERED,
]


def _ordered_menu_items(item_ids):
    items_map = MenuItem.objects.in_bulk(item_ids)
    return [items_map[item_id] for item_id in item_ids if item_id in items_map]


def _recent_seed_item_ids(user, limit=6):
    if not user or not user.is_authenticated:
        return []

    rows = (
        OrderItem.objects.filter(order__user=user, order__status__in=VALID_RECOMMENDATION_STATUSES)
        .values("item_id")
        .annotate(score=Sum("quantity"), orders=Count("order_id", distinct=True))
        .order_by("-orders", "-score")[:limit]
    )
    return [row["item_id"] for row in rows]


def _cooccurring_rows(seed_ids, exclude_ids=None, limit=6):
    if not seed_ids:
        return []

    exclude_ids = set(exclude_ids or [])
    order_ids = (
        OrderItem.objects.filter(order__status__in=VALID_RECOMMENDATION_STATUSES, item_id__in=seed_ids)
        .values_list("order_id", flat=True)
        .distinct()
    )
    return list(
        OrderItem.objects.filter(order__status__in=VALID_RECOMMENDATION_STATUSES, order_id__in=order_ids)
        .exclude(item_id__in=exclude_ids)
        .values("item_id", "item__category")
        .annotate(pair_orders=Count("order_id", distinct=True), total_qty=Sum("quantity"))
        .order_by("-pair_orders", "-total_qty")[: limit * 3]
    )


def _favorite_category_item_ids(user, exclude_ids=None, limit=6):
    if not user or not user.is_authenticated:
        return []

    exclude_ids = set(exclude_ids or [])
    category_rows = (
        OrderItem.objects.filter(order__user=user, order__status__in=VALID_RECOMMENDATION_STATUSES)
        .values("item__category")
        .annotate(score=Sum("quantity"))
        .order_by("-score")[:3]
    )

    item_ids = []
    for row in category_rows:
        category_ids = list(
            MenuItem.objects.filter(category=row["item__category"])
            .exclude(id__in=exclude_ids.union(item_ids))
            .values_list("id", flat=True)[:limit]
        )
        item_ids.extend(category_ids)
        if len(item_ids) >= limit:
            break

    return item_ids[:limit]


def _popular_item_ids(exclude_ids=None, limit=6):
    exclude_ids = set(exclude_ids or [])
    rows = (
        OrderItem.objects.filter(order__status__in=VALID_RECOMMENDATION_STATUSES)
        .exclude(item_id__in=exclude_ids)
        .values("item_id")
        .annotate(score=Sum("quantity"), orders=Count("order_id", distinct=True))
        .order_by("-score", "-orders")[: limit * 2]
    )
    item_ids = [row["item_id"] for row in rows]

    if len(item_ids) < limit:
        fallback_ids = list(
            MenuItem.objects.exclude(id__in=exclude_ids.union(item_ids))
            .values_list("id", flat=True)[: limit - len(item_ids)]
        )
        item_ids.extend(fallback_ids)

    return item_ids[:limit]


def _reason_from_context(dish, seed_items=None, cart_mode=False):
    seed_items = list(seed_items or [])

    for seed in seed_items:
        if dish.category == seed.category:
            return f"Because you ordered {seed.category_name.lower()}."

    if seed_items:
        return f"Frequently paired with {seed_items[0].name.lower()}."

    if cart_mode:
        return "Popular add-on with similar carts."

    return f"Recommended from our {dish.category_name.lower()} picks."


def _build_recommendation_cards(item_ids, seed_items=None, cart_mode=False, limit=6):
    dishes = _ordered_menu_items(item_ids[:limit])
    return [
        {
            "dish": dish,
            "reason": _reason_from_context(dish, seed_items=seed_items, cart_mode=cart_mode),
        }
        for dish in dishes
    ]


def get_personalized_recommendations(user=None, cart_items=None, limit=6):
    cart_items = list(cart_items or [])
    cart_item_ids = [cart.item_id for cart in cart_items]
    recent_seed_ids = _recent_seed_item_ids(user, limit=6)

    seed_ids = []
    for item_id in cart_item_ids + recent_seed_ids:
        if item_id not in seed_ids:
            seed_ids.append(item_id)

    seed_items = _ordered_menu_items(seed_ids[:3])
    exclude_ids = set(seed_ids)
    recommended_ids = []

    for row in _cooccurring_rows(seed_ids, exclude_ids=exclude_ids, limit=limit):
        item_id = row["item_id"]
        if item_id not in recommended_ids:
            recommended_ids.append(item_id)

    if len(recommended_ids) < limit:
        for item_id in _favorite_category_item_ids(
            user,
            exclude_ids=exclude_ids.union(recommended_ids),
            limit=limit - len(recommended_ids),
        ):
            if item_id not in recommended_ids:
                recommended_ids.append(item_id)

    if len(recommended_ids) < limit:
        for item_id in _popular_item_ids(
            exclude_ids=exclude_ids.union(recommended_ids),
            limit=limit - len(recommended_ids),
        ):
            if item_id not in recommended_ids:
                recommended_ids.append(item_id)

    seed_names = [item.name for item in seed_items]
    if cart_item_ids:
        subtitle = "Customers often pair these dishes with the items already in your cart."
    elif seed_names:
        subtitle = "Based on your previous orders, these dishes match your taste and ordering pattern."
    else:
        subtitle = "Popular combinations and customer favorites picked to make your next order easier."

    insight = ""
    if seed_names:
        insight = "Pairs well with " + ", ".join(seed_names[:2]) + "."

    return {
        "title": "Suggestions For You",
        "subtitle": subtitle,
        "insight": insight,
        "cards": _build_recommendation_cards(recommended_ids, seed_items=seed_items, cart_mode=bool(cart_item_ids), limit=limit),
    }


def get_frequently_bought_together(seed_item=None, cart_items=None, limit=3):
    cart_items = list(cart_items or [])
    seed_items = []

    if seed_item:
        seed_items.append(seed_item)
    for cart in cart_items:
        if cart.item not in seed_items:
            seed_items.append(cart.item)

    seed_ids = [item.id for item in seed_items]
    if not seed_ids:
        return None

    rows = _cooccurring_rows(seed_ids, exclude_ids=seed_ids, limit=limit)
    combo_ids = []
    for row in rows:
        if row["item_id"] not in combo_ids:
            combo_ids.append(row["item_id"])

    dishes = _ordered_menu_items(combo_ids[:limit])
    if not dishes:
        return None

    total_price = sum(float(item.price) for item in dishes)
    anchor = seed_items[0]

    return {
        "title": "Frequently Bought Together",
        "subtitle": f"Customers who order {anchor.name} often add these dishes too.",
        "seed_name": anchor.name,
        "items": dishes,
        "total_price": total_price,
    }


def get_item_detail_recommendations(item, user=None, limit=4):
    co_rows = _cooccurring_rows([item.id], exclude_ids={item.id}, limit=limit)
    recommended_ids = []
    for row in co_rows:
        if row["item_id"] not in recommended_ids:
            recommended_ids.append(row["item_id"])

    if len(recommended_ids) < limit:
        category_ids = list(
            MenuItem.objects.filter(category=item.category)
            .exclude(id__in={item.id}.union(recommended_ids))
            .values_list("id", flat=True)[: limit - len(recommended_ids)]
        )
        recommended_ids.extend(category_ids)

    return {
        "title": "You May Also Like",
        "subtitle": f"Chosen for guests who enjoy {item.name} and similar {item.category_name.lower()} dishes.",
        "cards": _build_recommendation_cards(recommended_ids, seed_items=[item], cart_mode=False, limit=limit),
    }
