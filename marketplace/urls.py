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
    path('toggle_wishlist/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),
    path('submit_review/<int:product_id>/', views.submit_review, name='submit_review'),
    path('notifications/', views.notifications, name='notifications'),
    path('get_notification_count/', views.get_notification_count, name='get_notification_count'),
    path('update_order_status/<int:order_id>/', views.update_order_status, name='update_order_status'),
    path('admin_delete_user/<int:user_id>/', views.admin_delete_user, name='admin_delete_user'),
    path('admin_delete_product/<int:product_id>/', views.admin_delete_product, name='admin_delete_product'),
]
