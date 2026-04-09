import json
import random

from django.http import JsonResponse
from django.shortcuts import render

from menu.models import MenuItem


EMOTION_TO_MOOD = {
    "happy": "chill",
    "sad": "comfort",
    "angry": "hungry",
    "surprised": "hungry",
    "fearful": "comfort",
    "disgusted": "healthy",
    "neutral": "healthy",
}

MOOD_PROFILES = {
    "hungry": {
        "categories": {"main_course", "biryani", "rice", "rolls"},
        "keywords": {"biryani", "thali", "butter", "fried", "curry", "masala", "meal", "gravy"},
        "description": "Big, filling dishes for strong cravings.",
    },
    "healthy": {
        "categories": {"south_indian", "beverages", "rice"},
        "keywords": {"salad", "grilled", "fresh", "lime", "tandoori", "steamed", "light", "soup"},
        "description": "Cleaner and lighter picks for a balanced mood.",
    },
    "chill": {
        "categories": {"snacks", "fast_food", "beverages", "desserts", "chinese"},
        "keywords": {"coffee", "fries", "noodles", "sandwich", "shake", "cold", "crispy", "comfort"},
        "description": "Relaxed comfort food for easy-going moments.",
    },
    "comfort": {
        "categories": {"main_course", "breads", "desserts", "beverages", "snacks"},
        "keywords": {"naan", "chai", "paratha", "dal", "paneer", "sweet", "lassi", "warm"},
        "description": "Warm and soothing food for a softer mood.",
    },
}

FALLBACK_ITEMS = [
    {"name": "Paneer Tikka", "price": 250, "is_veg": True, "moods": ["hungry"], "cal": "320 kcal"},
    {"name": "Veg Burger", "price": 150, "is_veg": True, "moods": ["chill"], "cal": "280 kcal"},
    {"name": "Chicken Biryani", "price": 350, "is_veg": False, "moods": ["hungry"], "cal": "500 kcal"},
    {"name": "Fruit Smoothie", "price": 170, "is_veg": True, "moods": ["healthy", "chill"], "cal": "150 kcal"},
    {"name": "Dal Khichdi", "price": 190, "is_veg": True, "moods": ["healthy", "comfort"], "cal": "210 kcal"},
    {"name": "Masala Chai", "price": 90, "is_veg": True, "moods": ["comfort"], "cal": "120 kcal"},
]


def mood_selector_page(request):
    return render(
        request,
        "menu/mood_selector.html",
        {
            "emotion_to_mood": EMOTION_TO_MOOD,
            "supported_moods": MOOD_PROFILES,
        },
    )


def _safe_budget(value, default=500):
    try:
        budget = int(value)
    except (TypeError, ValueError):
        return default
    return max(50, min(2000, budget))


def _normalize_emotion(emotion):
    return (emotion or "").strip().lower()


def _resolve_mood(payload):
    mood = (payload.get("mood") or "").strip().lower()
    emotion = _normalize_emotion(payload.get("detectedEmotion") or payload.get("detected_emotion"))
    derived = EMOTION_TO_MOOD.get(emotion)

    if mood == "auto":
        mood = derived or "chill"

    if mood not in MOOD_PROFILES:
        mood = derived or "hungry"

    return mood, emotion


def _score_item(item, mood):
    profile = MOOD_PROFILES.get(mood, {})
    score = 0
    text = f"{item.name} {item.description} {item.category}".lower()

    if item.category in profile.get("categories", set()):
        score += 5

    for keyword in profile.get("keywords", set()):
        if keyword in text:
            score += 2

    if item.price <= 250:
        score += 1

    if item.is_veg and mood in {"healthy", "comfort"}:
        score += 1

    return score


def _serialize_item(item, mood, score):
    image = ""
    if item.image:
        try:
            image = item.image.url
        except ValueError:
            image = ""

    category_label = item.category.replace("_", " ").title()
    insight_bits = [f"Fits a {mood} craving", f"{category_label} pick"]
    if score >= 7:
        insight_bits.insert(0, "Strong match")

    return {
        "name": item.name,
        "price": float(item.price),
        "image": image,
        "calories": "Chef pick",
        "desc": " . ".join(insight_bits) + ".",
    }


def _fallback_results(mood, veg, budget):
    filtered = [
        item for item in FALLBACK_ITEMS
        if item["price"] <= budget and (veg != "veg" or item["is_veg"])
    ]

    mood_match = [item for item in filtered if mood in item["moods"]]
    if mood_match:
        filtered = mood_match

    random.shuffle(filtered)
    return [
        {
            "name": item["name"],
            "price": item["price"],
            "image": "",
            "calories": item["cal"],
            "desc": f"Picked for a {mood} mood.",
        }
        for item in filtered[:5]
    ]


def get_suggestions(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON payload"}, status=400)

    mood, detected_emotion = _resolve_mood(payload)
    veg = (payload.get("veg") or "all").strip().lower()
    budget = _safe_budget(payload.get("budget", 500))
    detection_confidence = payload.get("detectionConfidence") or payload.get("detection_confidence")

    items = MenuItem.objects.all()
    if veg == "veg":
        items = items.filter(is_veg=True)
    items = items.filter(price__lte=budget)

    results = []
    if items.exists():
        ranked_items = list(items)
        ranked_items.sort(key=lambda item: (_score_item(item, mood), -float(item.price)), reverse=True)
        results = [_serialize_item(item, mood, _score_item(item, mood)) for item in ranked_items[:5]]
    else:
        results = _fallback_results(mood, veg, budget)

    profile = MOOD_PROFILES[mood]
    response = {
        "items": results,
        "mood": mood,
        "detected_emotion": detected_emotion,
        "detection_confidence": detection_confidence,
        "insight": profile["description"],
    }
    return JsonResponse(response)
