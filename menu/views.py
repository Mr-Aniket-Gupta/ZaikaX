from .models import MenuItem
from django.shortcuts import render

def menu_list(request):
    context = {
        'starters': MenuItem.objects.filter(category='starters'),
        'main_course': MenuItem.objects.filter(category='main_course'),
        'biryani': MenuItem.objects.filter(category='biryani'),
        'breads': MenuItem.objects.filter(category='breads'),
        'rice_and_noodles': MenuItem.objects.filter(category='rice'),
        'snacks': MenuItem.objects.filter(category='snacks'),
        'beverages': MenuItem.objects.filter(category='beverages'),
        'desserts': MenuItem.objects.filter(category='desserts'),
    }

    # Choose a featured menu item (prefer items with images) from categories shown on the page
    visible_categories = ['starters', 'main_course', 'biryani']
    featured = MenuItem.objects.filter(category__in=visible_categories, image__isnull=False).order_by('?').first()
    if not featured:
        # fallback to any menu item with an image
        featured = MenuItem.objects.filter(image__isnull=False).order_by('?').first()
    context['featured'] = featured

    # Load a few recent customer reviews to display below the menu (show up to 6)
    from main.models import Review
    reviews_list = Review.objects.all()[:6]
    context['reviews_list'] = reviews_list

    return render(request, 'main/menu_list.html', context)


def menu_3d(request):
    """Render a simple 3D gallery where each menu item is represented
    as a textured 3D card built from the item's image."""
    items = MenuItem.objects.all()
    return render(request, 'menu/3d_gallery.html', {'items': items})
