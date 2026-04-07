from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='admin_dashboard'),

    path('login/', views.admin_login, name='admin_login'),
    path('logout/', views.admin_logout, name='admin_logout'),

    path('menu/', views.menu_list, name='admin_menu'),
    path('categories/', views.category_list, name='admin_categories'),
    path('categories/add/', views.add_category, name='add_category'),
    path('categories/edit/<int:category_id>/', views.edit_category, name='edit_category'),
    path('categories/delete/<int:category_id>/', views.delete_category, name='delete_category'),
    path('menu/add/', views.add_dish, name='add_dish'),
    path('menu/edit/<int:id>/', views.edit_dish, name='edit_dish'),
    path('orders/', views.orders, name='admin_orders'),
    path('offers/', views.offers, name='admin_offers'),
    path('offers/add/', views.add_offer, name='add_offer'),
    path('offers/<int:coupon_id>/update/', views.update_offer, name='update_offer'),
    path('offers/<int:coupon_id>/delete/', views.delete_offer, name='delete_offer'),
    path('recipes/', views.recipe_shares, name='admin_recipes'),
    path('recipe-orders/', views.recipe_order_requests, name='admin_recipe_orders'),
    path('recipe-orders/<int:request_id>/update/', views.update_recipe_order_request, name='update_recipe_order_request'),
    path('sales-data/', views.sales_data, name='admin_sales_data'),
    path('dashboard-data/', views.dashboard_analytics_data, name='admin_dashboard_data'),
    path('users/', views.users, name='admin_users'),
    path('users/assign/<int:user_id>/', views.assign_admin_assistant, name='assign_admin_assistant'),
    path('profile/', views.profile, name='admin_profile'),
    path('users/remove/<int:user_id>/', views.remove_admin_assistant, name='remove_admin_assistant'),
    path('menu/delete/<int:id>/', views.delete_dish, name='delete_dish'),
    path('orders/update/<int:order_id>/', views.update_order_status, name='update_order_status'),
]
