import os
import random
import re
from pathlib import Path

import django
from django.conf import settings

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ZaikaX.settings')
django.setup()

from menu.models import Category, MenuItem, DEFAULT_CATEGORY_META
from menu.menu_data import MENU_DATA


def _normalize(text):
    return re.sub(r'[^a-z0-9]+', '', text.lower())


def _find_media_menu_dir(base_dir):
    """Find media/menu across common project layouts."""
    candidates = [
        Path(getattr(settings, 'MEDIA_ROOT', '')) / 'menu',
        base_dir / 'media' / 'menu',
        base_dir / 'ZaikaX' / 'media' / 'menu',
    ]

    seen = set()
    for path in candidates:
        if not path:
            continue
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.exists() and resolved.is_dir():
            return resolved

    return None


def _build_media_index(media_menu_dir):
    valid_ext = {'.png', '.jpg', '.jpeg', '.webp', '.gif'}
    files = [f for f in media_menu_dir.iterdir() if f.is_file() and f.suffix.lower() in valid_ext]
    index = {}
    for f in files:
        key = _normalize(f.stem)
        index.setdefault(key, []).append(f.name)
    return files, index


def _resolve_image(item_name, image_path, media_files, media_index):
    # Manual overrides for common naming mismatches
    manual = {
        'Paneer Tikka': 'Paneer_tikka_masala.jpg',
        'Dal Makhani': 'Dal_tadka.png',
    }
    if item_name in manual:
        return manual[item_name]

    candidates = []
    candidates.append(_normalize(item_name))

    if image_path:
        image_stem = Path(image_path).stem
        candidates.append(_normalize(image_stem))

    # Exact normalized match
    for c in candidates:
        if c in media_index:
            return media_index[c][0]

    # Fuzzy token match
    words = [w.lower() for w in re.findall(r'[a-zA-Z0-9]+', item_name)]
    for f in media_files:
        stem = f.stem.lower().replace('_', ' ')
        if all(w in stem for w in words if len(w) > 2):
            return f.name

    return None


def _pick_fallback_image(name, category, is_veg, available_images, used_images):
    """Pick the most relevant unused image instead of fully random selection."""
    unused = [f for f in available_images if f.name not in used_images]
    if not unused:
        return None

    category_keywords = {
        'starters': {'starter', 'tikka', 'kabab', 'manchurian', 'crispy', 'snack'},
        'main_course': {'curry', 'masala', 'paneer', 'chicken', 'mutton', 'dal', 'main'},
        'biryani': {'biryani', 'rice', 'dum'},
        'breads': {'naan', 'roti', 'paratha', 'bread'},
        'rice': {'rice', 'pulao', 'fried', 'jeera'},
        'snacks': {'fries', 'sandwich', 'samosa', 'kachori', 'snack'},
        'beverages': {'chai', 'lassi', 'drink', 'juice', 'soda', 'thandai'},
        'desserts': {'gulab', 'jamun', 'kulfi', 'rasmalai', 'dessert', 'sweet'},
    }
    non_veg_tokens = {'chicken', 'mutton', 'fish', 'egg', 'meat'}

    item_tokens = set(re.findall(r'[a-z0-9]+', name.lower()))
    cat_tokens = category_keywords.get(category, set())

    best_file = None
    best_score = -10**9
    for f in unused:
        stem_tokens = set(re.findall(r'[a-z0-9]+', f.stem.lower().replace('_', ' ')))
        score = 0

        # Prefer overlap with dish words and category words.
        score += len(item_tokens & stem_tokens) * 5
        score += len(cat_tokens & stem_tokens) * 3

        has_non_veg = bool(stem_tokens & non_veg_tokens)
        if is_veg and has_non_veg:
            score -= 6
        if (not is_veg) and has_non_veg:
            score += 4

        # Slightly prefer clearer filenames over generic assets.
        if 'hero' in stem_tokens or 'main' in stem_tokens:
            score -= 2

        if score > best_score:
            best_score = score
            best_file = f

    return best_file.name if best_file else None


def _extract_item_fields(item):
    """Return normalized item fields for dict- and tuple-based menu data."""
    if isinstance(item, dict):
        return (
            item.get('name', ''),
            item.get('description', ''),
            item.get('price', 0),
            item.get('is_veg', True),
            item.get('image'),
        )

    # Backward compatibility: (name, description, price, is_veg, image)
    return item


def seed_menu():
    """Populate MenuItem table using menu_data.py and images from media/menu."""
    base_dir = Path(__file__).resolve().parent
    media_menu_dir = _find_media_menu_dir(base_dir)

    if not media_menu_dir:
        print(
            "Media folder not found. Checked: "
            f"{Path(getattr(settings, 'MEDIA_ROOT', '')) / 'menu'}, "
            f"{base_dir / 'media' / 'menu'}, "
            f"{base_dir / 'ZaikaX' / 'media' / 'menu'}"
        )
        return

    media_files, media_index = _build_media_index(media_menu_dir)
    
    available_images = list(media_files)  # Copy for random selection
    used_images = set()

    for index, category_slug in enumerate(MENU_DATA.keys(), start=1):
        meta = DEFAULT_CATEGORY_META.get(category_slug, {})
        Category.objects.get_or_create(
            slug=category_slug,
            defaults={
                "name": meta.get("name", category_slug.replace("_", " ").title()),
                "icon": meta.get("icon", "🍽"),
                "display_order": meta.get("display_order", index * 10),
            },
        )

    # Clear existing menu items for clean reseed
    deleted_count, _ = MenuItem.objects.all().delete()
    print(f"Cleared existing menu items. Deleted records: {deleted_count}")

    created = 0
    with_image = 0
    exact_match = 0
    fuzzy_match = 0
    random_assigned = 0
    missing_images = []
    existing_names = {
        _extract_item_fields(item)[0]
        for items in MENU_DATA.values()
        for item in items
    }

    for category, items in MENU_DATA.items():
        for item in items:
            name, description, price, is_veg, image_path = _extract_item_fields(item)
            matched_image = _resolve_image(name, image_path, media_files, media_index)

            image_used = matched_image

            if matched_image:
                # Check if exact or fuzzy
                norm_name = _normalize(name)
                norm_image = _normalize(Path(matched_image).stem)
                if norm_name == norm_image:
                    exact_match += 1
                else:
                    fuzzy_match += 1
                used_images.add(matched_image)
            elif available_images:
                # Fallback to best unused image based on dish/category hints.
                image_used = _pick_fallback_image(
                    name=name,
                    category=category,
                    is_veg=is_veg,
                    available_images=available_images,
                    used_images=used_images,
                )
                if image_used:
                    used_images.add(image_used)
                    random_assigned += 1

            MenuItem.objects.create(
                name=name,
                description=description,
                price=price,
                category=category,
                is_veg=is_veg,
                image=f"menu/{image_used}" if image_used else ''
            )

            created += 1
            if image_used:
                with_image += 1
                extra_note = " (random fallback)" if not matched_image else ""
                print(f"Added: {name} -> menu/{image_used}{extra_note}")
            else:
                missing_images.append(name)
                print(f"Added: {name} -> no image")

    # Ensure a minimum dataset size by using still-unused images.
    category_choices = list(Category.objects.values_list("slug", flat=True))
    extra_index = 1
    while created < 50 and available_images:
        unused = [f for f in available_images if f.name not in used_images]
        if not unused:
            break

        extra_image = random.choice(unused).name
        used_images.add(extra_image)

        mains = ['Veg', 'Chicken', 'Paneer', 'Dal', 'Rice']
        adjs = ['Special', 'Masala', 'Fried', 'Curry', 'Grilled']
        main = random.choice(mains)
        adj = random.choice(adjs)

        extra_name = f"{adj} {main} Dish {extra_index}"
        while extra_name in existing_names:
            extra_index += 1
            extra_name = f"{adj} {main} Dish {extra_index}"

        existing_names.add(extra_name)
        extra_desc = f"Delicious {main.lower()} preparation with authentic spices."
        extra_price = random.randint(150, 450)
        extra_veg = random.choice([True, False])
        extra_cat = random.choice(category_choices)

        MenuItem.objects.create(
            name=extra_name,
            description=extra_desc,
            price=extra_price,
            category=extra_cat,
            is_veg=extra_veg,
            image=f"menu/{extra_image}"
        )
        created += 1
        with_image += 1
        extra_index += 1
        print(f"Generated extra: {extra_name} -> menu/{extra_image}")

    print("\nMenu seeding complete!")
    print(f"Total items created: {created}")
    print(f"Items with image: {with_image}")
    print(f"Items without image: {created - with_image}")
    print(f"Exact image matches: {exact_match}")
    print(f"Fuzzy/manual image matches: {fuzzy_match}")
    print(f"Random fallback assignments: {random_assigned}")

    if missing_images:
        print("\nMissing image for:")
        for item_name in missing_images:
            print(f"- {item_name}")


if __name__ == '__main__':
    seed_menu()
