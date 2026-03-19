import os
import re
from pathlib import Path

import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ZaikaX.settings')
django.setup()

from menu.models import MenuItem
from menu.menu_data import MENU_DATA


def _normalize(text):
    return re.sub(r'[^a-z0-9]+', '', text.lower())


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


def seed_menu():
    """Populate MenuItem table using menu_data.py and images from media/menu."""
    base_dir = Path(__file__).resolve().parent
    media_menu_dir = base_dir / 'media' / 'menu'

    if not media_menu_dir.exists():
        print(f"Media folder not found: {media_menu_dir}")
        return

    media_files, media_index = _build_media_index(media_menu_dir)

    # Clear existing menu items for clean reseed
    deleted_count, _ = MenuItem.objects.all().delete()
    print(f"Cleared existing menu items. Deleted records: {deleted_count}")

    created = 0
    with_image = 0
    missing_images = []

    for category, items in MENU_DATA.items():
        for name, description, price, is_veg, image_path in items:
            matched_image = _resolve_image(name, image_path, media_files, media_index)

            MenuItem.objects.create(
                name=name,
                description=description,
                price=price,
                category=category,
                is_veg=is_veg,
                image=f"menu/{matched_image}" if matched_image else ''
            )

            created += 1
            if matched_image:
                with_image += 1
                print(f"Added: {name} -> menu/{matched_image}")
            else:
                missing_images.append(name)
                print(f"Added: {name} -> (no image found in media/menu)")

    print("\nMenu seeding complete!")
    print(f"Total items created: {created}")
    print(f"Items with image: {with_image}")
    print(f"Items without image: {created - with_image}")

    if missing_images:
        print("\nMissing image for:")
        for item_name in missing_images:
            print(f"- {item_name}")


if __name__ == '__main__':
    seed_menu()
