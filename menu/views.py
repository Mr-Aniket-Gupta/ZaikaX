from django.shortcuts import get_object_or_404, render

from .models import Category, MenuItem
from main.recommendations import (
    get_frequently_bought_together,
    get_item_detail_recommendations,
    get_personalized_recommendations,
)


def menu_list(request):
    category_sections = []
    for category in Category.objects.all():
        items = MenuItem.objects.filter(category=category.slug)
        if not items.exists():
            continue

        category_sections.append({
            "slug": category.slug,
            "anchor": category.slug.replace("_", "-"),
            "name": category.name,
            "icon": category.icon or "🍽",
            "items": items,
        })

    visible_category_slugs = [section["slug"] for section in category_sections[:3]]
    featured = (
        MenuItem.objects.filter(category__in=visible_category_slugs, image__isnull=False)
        .exclude(image="")
        .order_by("?")
        .first()
    )
    if not featured:
        featured = MenuItem.objects.filter(image__isnull=False).exclude(image="").order_by("?").first()

    from main.models import Review

    context = {
        "category_sections": category_sections,
        "featured": featured,
        "reviews_list": Review.objects.all()[:6],
        "recommendations": get_personalized_recommendations(request.user, limit=4),
        "frequently_bought_together": get_frequently_bought_together(seed_item=featured, limit=3) if featured else None,
    }
    return render(request, "main/menu_list_dynamic.html", context)


def menu_item_detail(request, item_id):
    item = get_object_or_404(MenuItem, id=item_id)
    context = {
        "item": item,
        "recommendations": get_item_detail_recommendations(item, user=request.user, limit=4),
        "frequently_bought_together": get_frequently_bought_together(seed_item=item, limit=3),
    }
    return render(request, "main/menu_item_detail.html", context)


def menu_3d(request):
    """Render a simple 3D gallery where each menu item is represented
    as a textured 3D card built from the item's image."""
    items = MenuItem.objects.all()
    return render(request, "menu/3d_gallery.html", {"items": items})
