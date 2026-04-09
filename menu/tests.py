import json

from django.test import TestCase
from django.urls import reverse

from .models import MenuItem


class MoodSuggestionTests(TestCase):
    def setUp(self):
        MenuItem.objects.create(
            name="Comfort Dal",
            description="Warm dal with homestyle spices",
            price=180,
            category="main_course",
            is_veg=True,
        )
        MenuItem.objects.create(
            name="Fresh Lime Soda",
            description="Fresh and light drink",
            price=90,
            category="beverages",
            is_veg=True,
        )

    def test_auto_detected_emotion_maps_to_expected_mood(self):
        response = self.client.post(
            reverse("mood_suggest"),
            data=json.dumps(
                {
                    "mood": "auto",
                    "detectedEmotion": "sad",
                    "veg": "all",
                    "budget": 300,
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["mood"], "comfort")
        self.assertEqual(payload["detected_emotion"], "sad")
        self.assertTrue(payload["items"])

    def test_veg_filter_excludes_non_veg_items(self):
        MenuItem.objects.create(
            name="Chicken Biryani",
            description="Filling biryani meal",
            price=250,
            category="biryani",
            is_veg=False,
        )

        response = self.client.post(
            reverse("mood_suggest"),
            data=json.dumps(
                {
                    "mood": "hungry",
                    "veg": "veg",
                    "budget": 300,
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        names = [item["name"] for item in response.json()["items"]]
        self.assertNotIn("Chicken Biryani", names)
