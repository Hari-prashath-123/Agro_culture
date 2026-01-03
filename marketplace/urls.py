from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('farmer_dashboard/', views.farmer_products, name='farmer_dashboard'),
    path('buyer_dashboard/', views.buyer_dashboard, name='buyer_dashboard'),
    path('login/', views.unified_login, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('admin_summary/', views.admin_summary, name='admin_summary'),
    path('password_change/', auth_views.PasswordChangeView.as_view(template_name='registration/password_change_form.html', success_url='/'), name='password_change'),
    path('farmer_products/', views.farmer_products, name='farmer_products'),
    path('add_product/', views.add_product, name='add_product'),
    path('order_history/', views.order_history, name='order_history'),
]
