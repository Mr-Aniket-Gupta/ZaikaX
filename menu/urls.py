from django.urls import path
from .views import menu_list, menu_3d
from .views_ai import mood_selector_page, get_suggestions


urlpatterns = [
    path('', menu_list, name='menu_list'),
    path('3d/', menu_3d, name='menu_3d'),
    path("mood/", mood_selector_page, name="mood_selector"),
    path("mood/suggest/", get_suggestions, name="mood_suggest"),
]
