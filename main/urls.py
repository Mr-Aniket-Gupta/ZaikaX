from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='home'),


    # Extra pages
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),

    # Authentication
    path('login/', views.login_user, name='login'),
    path('register/', views.register_user, name='register'),
    path('logout/', views.logout_user, name='logout'),
    # path('verify-otp/', views.verify_otp, name='verify_otp'),

    

    # Chatbot / FAQ API
    path('faq-search/', views.faq_search, name='faq_search'),
    path('faq-reply/', views.faq_reply, name='faq_reply'),
]

