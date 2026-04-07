from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='home'),


    # Extra pages
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('recipes/', views.recipes, name='recipes'),
    path('recipes/share/', views.share_recipe, name='share_recipe'),
    path('recipes/orders/', views.my_recipe_orders, name='my_recipe_orders'),
    path('recipes/orders/<int:request_id>/accept/', views.accept_recipe_quote, name='accept_recipe_quote'),
    path('recipes/<int:recipe_id>/', views.recipe_detail, name='recipe_detail'),
    path('recipes/<int:recipe_id>/react/', views.react_to_recipe, name='react_to_recipe'),
    path('recipes/<int:recipe_id>/request-order/', views.request_recipe_order, name='request_recipe_order'),

    # Authentication
    path('login/', views.login_user, name='login'),
    path('register/', views.register_user, name='register'),
    path('logout/', views.logout_user, name='logout'),
    path('profile/', views.user_profile, name='user_profile'),
    path('profile/address/<int:address_id>/delete/', views.delete_address, name='delete_address'),
    path('profile/address/<int:address_id>/default/', views.set_default_address, name='set_default_address'),
    # path('verify-otp/', views.verify_otp, name='verify_otp'),

    

    # Chatbot / FAQ API
    path('faq-search/', views.faq_search, name='faq_search'),
    path('faq-reply/', views.faq_reply, name='faq_reply'),
]

