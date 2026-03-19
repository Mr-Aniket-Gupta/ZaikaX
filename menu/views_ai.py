import json
import requests
import random
from django.http import JsonResponse
from django.shortcuts import render
from menu.models import MenuItem



# 🔹 PAGE
def mood_selector_page(request):
    return render(request, "menu/mood_selector.html")


def get_suggestions(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            mood = data.get("mood")
            veg = data.get("veg")

            try:
                budget = int(data.get("budget", 500))
            except:
                budget = 500

            items = MenuItem.objects.all()

            # =====================================================
            # 🔴 MOCK DATA
            # =====================================================
            if not items.exists():

                mock_items = [
                    {"name": "Paneer Tikka", "price": 250, "is_veg": True, "mood": ["party", "hungry"], "cal": 320},
                    {"name": "Veg Burger", "price": 150, "is_veg": True, "mood": ["chill", "quick"], "cal": 280},
                    {"name": "Pizza", "price": 300, "is_veg": True, "mood": ["party", "hungry"], "cal": 400},
                    {"name": "Pasta", "price": 280, "is_veg": True, "mood": ["chill"], "cal": 350},
                    {"name": "French Fries", "price": 120, "is_veg": True, "mood": ["chill", "quick"], "cal": 300},
                    {"name": "Cold Coffee", "price": 130, "is_veg": True, "mood": ["chill"], "cal": 220},
                    {"name": "Chocolate Shake", "price": 160, "is_veg": True, "mood": ["chill"], "cal": 350},
                    {"name": "Chicken Biryani", "price": 350, "is_veg": False, "mood": ["hungry"], "cal": 500},
                    {"name": "Grilled Chicken", "price": 400, "is_veg": False, "mood": ["healthy"], "cal": 280},
                    {"name": "Egg Roll", "price": 180, "is_veg": False, "mood": ["quick"], "cal": 320},
                    {"name": "Salad Bowl", "price": 200, "is_veg": True, "mood": ["healthy"], "cal": 180},
                    {"name": "Fruit Smoothie", "price": 170, "is_veg": True, "mood": ["healthy", "chill"], "cal": 150},
                    {"name": "Momos", "price": 140, "is_veg": False, "mood": ["quick", "chill"], "cal": 260},
                    {"name": "Sandwich", "price": 130, "is_veg": True, "mood": ["quick"], "cal": 240},
                    {"name": "Paneer Wrap", "price": 220, "is_veg": True, "mood": ["quick", "hungry"], "cal": 330},
                    {"name": "Dal Khichdi", "price": 190, "is_veg": True, "mood": ["healthy"], "cal": 210},
                    {"name": "Ice Cream", "price": 110, "is_veg": True, "mood": ["chill"], "cal": 270},
                    {"name": "Chicken Wings", "price": 320, "is_veg": False, "mood": ["party"], "cal": 450},
                    {"name": "Maggi", "price": 90, "is_veg": True, "mood": ["quick", "chill"], "cal": 250},
                    {"name": "Soup", "price": 140, "is_veg": True, "mood": ["healthy"], "cal": 120},
                ]

                filtered = mock_items

                # ✅ STEP 1: BUDGET FILTER
                

                # ✅ STEP 2: VEG FILTER
                if veg == "veg":
                    filtered = [i for i in filtered if i["is_veg"]]

                # ✅ STEP 3: MOOD FILTER (STRICT)
                if mood:
                    mood_filtered = [i for i in filtered if mood in i["mood"]]

                    # only fallback if NOTHING found
                    if mood_filtered:
                        filtered = mood_filtered
                        
                filtered = [i for i in filtered if i["price"] <= budget]
                # ❌ REMOVE SORTING (THIS WAS YOUR BUG)

                # ✅ RANDOMIZE ONLY
                random.shuffle(filtered)
                filtered = filtered[:5]

                results = []

                for item in filtered:

                    ai_text = f"{item['cal']} kcal\nPerfect for {mood or 'your mood'}"

                    results.append({
                        "name": item["name"],
                        "price": item["price"],
                        "image": "",
                        "calories": ai_text.split("\n")[0],
                        "desc": ai_text.split("\n")[1]
                    })

                return JsonResponse({"items": results})

            # =====================================================
            # 🟢 REAL DB
            # =====================================================

            filtered = items

            if budget:
                filtered = filtered.filter(price__lte=budget)

            if veg == "veg" and hasattr(MenuItem, "is_veg"):
                filtered = filtered.filter(is_veg=True)

            # ⚠️ DB DOESN'T HAVE MOOD FIELD → so skip mood filtering
            # otherwise you'll get empty results again

            filtered = list(filtered)
            random.shuffle(filtered)
            filtered = filtered[:5]

            results = []

            for item in filtered:
                image = ""
                if item.image:
                    try:
                        image = item.image.url
                    except:
                        pass

                results.append({
                    "name": item.name,
                    "price": item.price,
                    "image": image,
                    "calories": "300 kcal",
                    "desc": "Recommended for you"
                })

            return JsonResponse({"items": results})

        except Exception as e:
            print("ERROR:", e)
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=400)