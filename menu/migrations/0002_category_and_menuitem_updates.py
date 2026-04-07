from django.db import migrations, models


DEFAULT_CATEGORY_META = {
    "starters": {"name": "Starters", "icon": "🥗", "display_order": 10},
    "main_course": {"name": "Main Course", "icon": "🍛", "display_order": 20},
    "biryani": {"name": "Biryani", "icon": "🍚", "display_order": 30},
    "breads": {"name": "Breads", "icon": "🍞", "display_order": 40},
    "rice": {"name": "Rice & Noodles", "icon": "🍜", "display_order": 50},
    "snacks": {"name": "Snacks", "icon": "🥟", "display_order": 60},
    "beverages": {"name": "Beverages", "icon": "🥤", "display_order": 70},
    "desserts": {"name": "Desserts", "icon": "🍰", "display_order": 80},
    "chinese": {"name": "Chinese", "icon": "🥡", "display_order": 90},
    "south_indian": {"name": "South Indian", "icon": "🥞", "display_order": 100},
    "rolls": {"name": "Rolls", "icon": "🌯", "display_order": 110},
    "fast_food": {"name": "Fast Food", "icon": "🍟", "display_order": 120},
}


def seed_categories(apps, schema_editor):
    Category = apps.get_model("menu", "Category")
    MenuItem = apps.get_model("menu", "MenuItem")

    slugs = set(MenuItem.objects.values_list("category", flat=True))
    slugs.update(DEFAULT_CATEGORY_META.keys())

    for index, slug in enumerate(sorted(slugs), start=1):
        meta = DEFAULT_CATEGORY_META.get(slug, {})
        Category.objects.get_or_create(
            slug=slug,
            defaults={
                "name": meta.get("name", slug.replace("_", " ").title()),
                "icon": meta.get("icon", "🍽"),
                "display_order": meta.get("display_order", index * 10),
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ("menu", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, unique=True)),
                ("slug", models.SlugField(max_length=100, unique=True)),
                ("icon", models.CharField(blank=True, default="🍽", max_length=10)),
                ("display_order", models.PositiveIntegerField(default=100)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name_plural": "Categories",
                "ordering": ("display_order", "name"),
            },
        ),
        migrations.AlterField(
            model_name="menuitem",
            name="category",
            field=models.CharField(db_index=True, max_length=50),
        ),
        migrations.AlterModelOptions(
            name="menuitem",
            options={"ordering": ("name",)},
        ),
        migrations.RunPython(seed_categories, migrations.RunPython.noop),
    ]
