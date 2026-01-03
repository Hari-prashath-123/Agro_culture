from django.urls import path
from . import views

urlpatterns = [
    path('farmer_dashboard/', views.farmer_dashboard, name='farmer_dashboard'),
    path('buyer_dashboard/', views.buyer_dashboard, name='buyer_dashboard'),
    path('login/', views.unified_login, name='login'),
    path('register/', views.register, name='register'),
    path('admin_summary/', views.admin_summary, name='admin_summary'),
]
