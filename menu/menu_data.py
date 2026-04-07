from typing import TypedDict

class MenuItem(TypedDict):
    name: str
    description: str
    price: int
    is_veg: bool
    image: str | None


MENU_DATA: dict[str, list[MenuItem]] = {
    "starters": [
        {"name": "Paneer Tikka", "description": "Grilled cottage cheese marinated in spices", "price": 280, "is_veg": True, "image": "starters/paneer_tikka.jpg"},
        {"name": "Chicken Tandoori", "description": "Classic clay-oven roasted chicken", "price": 350, "is_veg": False, "image": "starters/chicken_tandoori.jpg"},
        {"name": "Hara Bhara Kabab", "description": "Healthy pan-fried green vegetable cutlets", "price": 220, "is_veg": True, "image": "starters/hara_bhara_kabab.jpg"},
        {"name": "Crispy Chicken", "description": "Deep-fried chicken strips with schezwan sauce", "price": 290, "is_veg": False, "image": "starters/crispy_chicken.jpg"},
        {"name": "Veg Manchurian", "description": "Indo-Chinese fried vegetable balls in gravy", "price": 250, "is_veg": True, "image": "starters/veg_manchurian.jpg"},
    ],
    "main_course": [
        {"name": "Butter Chicken", "description": "Smoky chicken in a creamy tomato gravy", "price": 420, "is_veg": False, "image": "main_course/butter_chicken.jpg"},
        {"name": "Paneer Butter Masala", "description": "Rich paneer cubes in tomato gravy", "price": 380, "is_veg": True, "image": "main_course/paneer_butter_masala.jpg"},
        {"name": "Dal Makhani", "description": "Creamy black lentils cooked overnight", "price": 320, "is_veg": True, "image": "main_course/dal_makhani.jpg"},
        {"name": "Mutton Rogan Josh", "description": "Kashmiri style mutton curry", "price": 480, "is_veg": False, "image": "main_course/mutton_rogan_josh.jpg"},
        {"name": "Palak Paneer", "description": "Paneer cubes in a creamy spinach gravy", "price": 360, "is_veg": True, "image": "main_course/palak_paneer.jpg"},
    ],
    "biryani": [
        {"name": "Veg Biryani", "description": "Aromatic basmati rice with mixed vegetables", "price": 300, "is_veg": True, "image": "biryani/veg_biryani.jpg"},
        {"name": "Chicken Biryani", "description": "Spicy dum cooked chicken and rice", "price": 380, "is_veg": False, "image": "biryani/chicken_biryani.jpg"},
        {"name": "Mutton Biryani", "description": "Rich rice with tender mutton pieces", "price": 450, "is_veg": False, "image": "biryani/mutton_biryani.jpg"},
    ],
    "breads": [
        {"name": "Butter Naan", "description": "Soft & buttery Indian flatbread", "price": 60, "is_veg": True, "image": "breads/butter_naan.jpg"},
        {"name": "Garlic Naan", "description": "Naan flavored with chopped garlic", "price": 80, "is_veg": True, "image": "breads/garlic_naan.jpg"},
        {"name": "Tandoori Roti", "description": "Whole wheat flatbread from clay oven", "price": 40, "is_veg": True, "image": "breads/tandoori_roti.jpg"},
    ],
    "desserts": [
        {"name": "Gulab Jamun", "description": "Sweet deep-fried milk dumplings", "price": 150, "is_veg": True, "image": "desserts/gulab_jamun.jpg"},
        {"name": "Rasmalai", "description": "Spongy cheese patties in sweetened milk", "price": 180, "is_veg": True, "image": "desserts/rasmalai.jpg"},
        {"name": "Kulfi", "description": "Traditional Indian ice cream", "price": 120, "is_veg": True, "image": "desserts/kulfi.jpg"},
    ],
    "beverages": [
        {"name": "Masala Chai", "description": "Spiced Indian tea with milk", "price": 80, "is_veg": True, "image": "beverages/masala_chai.jpg"},
        {"name": "Lassi", "description": "Sweet or salted yogurt drink", "price": 120, "is_veg": True, "image": "beverages/lassi.jpg"},
    ],
    "chinese": [
        {"name": "Hakka Noodles (Veg)", "description": "Stir-fried noodles with vegetables in Chinese sauce", "price": 260, "is_veg": True, "image": None},
        {"name": "Chicken Fried Rice", "description": "Fragrant rice with chicken and veggies", "price": 280, "is_veg": False, "image": None},
        {"name": "Chilli Paneer Dry", "description": "Crispy paneer tossed in spicy chilli sauce", "price": 320, "is_veg": True, "image": None},
        {"name": "Veg Fried Rice", "description": "Steamed rice with vegetables and soy sauce", "price": 240, "is_veg": True, "image": None},
        {"name": "Chicken Hakka Noodles", "description": "Noodles with shredded chicken and veggies", "price": 290, "is_veg": False, "image": None},
        {"name": "Gobi Manchurian", "description": "Crispy cauliflower in manchurian sauce", "price": 270, "is_veg": True, "image": None},
        {"name": "Chicken Manchurian", "description": "Gravy balls made from chicken", "price": 310, "is_veg": False, "image": None},
        {"name": "American Chopsuey", "description": "Crispy noodles with sweet n sour veggies", "price": 300, "is_veg": True, "image": None},
    ],
    "south_indian": [
        {"name": "Vada Pav", "description": "Spicy potato fritter in pav bun", "price": 120, "is_veg": True, "image": None},
        {"name": "Plain Dosa", "description": "Crispy fermented rice-lentil crepe", "price": 100, "is_veg": True, "image": None},
        {"name": "Masala Dosa", "description": "Dosa stuffed with spiced potatoes", "price": 150, "is_veg": True, "image": None},
        {"name": "Idli Sambhar", "description": "Steamed rice cakes with lentil curry", "price": 110, "is_veg": True, "image": None},
        {"name": "Onion Uttapam", "description": "Thick pancake topped with onions", "price": 130, "is_veg": True, "image": None},
        {"name": "Mysore Masala Dosa", "description": "Dosa with spicy red chutney filling", "price": 170, "is_veg": True, "image": None},
    ],
    "rolls": [
        {"name": "Veg Roll", "description": "Fresh vegetables wrapped in rumali roti", "price": 200, "is_veg": True, "image": None},
        {"name": "Chicken Roll", "description": "Minced chicken keema in thin roti", "price": 240, "is_veg": False, "image": None},
        {"name": "Paneer Roll", "description": "Spiced paneer tikka in rumali roti", "price": 230, "is_veg": True, "image": None},
        {"name": "Aloo Roll", "description": "Spicy mashed potato roll", "price": 180, "is_veg": True, "image": None},
        {"name": "Schezwan Paneer Roll", "description": "Schezwan flavored paneer roll", "price": 250, "is_veg": True, "image": None},
    ],
    "rice": [
        {"name": "Jeera Rice", "description": "Basmati rice tempered with cumin", "price": 160, "is_veg": True, "image": None},
        {"name": "Steamed Rice", "description": "Plain basmati rice", "price": 120, "is_veg": True, "image": None},
        {"name": "Veg Pulao", "description": "Rice cooked with vegetables and spices", "price": 200, "is_veg": True, "image": None},
        {"name": "Schezwan Fried Rice", "description": "Spicy Chinese style fried rice", "price": 250, "is_veg": True, "image": None},
    ],
    "fast_food": [
        {"name": "French Fries", "description": "Crispy golden french fries", "price": 150, "is_veg": True, "image": None},
        {"name": "Veg Grilled Sandwich", "description": "Toasted sandwich with vegetables", "price": 160, "is_veg": True, "image": None},
        {"name": "Chicken Grilled Sandwich", "description": "Grilled sandwich with chicken", "price": 190, "is_veg": False, "image": None},
        {"name": "Samosa (2 pcs)", "description": "Crispy fried pastries with potato filling", "price": 80, "is_veg": True, "image": None},
        {"name": "Kachori (2 pcs)", "description": "Deep fried lentil stuffed pastries", "price": 90, "is_veg": True, "image": None},
    ],
}
