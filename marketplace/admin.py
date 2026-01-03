from django.contrib import admin
from .models import Product, Order, UserProfile, Wishlist, Review, Notification

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
	list_display = ('name', 'category', 'price', 'quantity', 'farmer')
	search_fields = ('name', 'category', 'farmer__username')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
	list_display = ('id', 'buyer', 'product', 'quantity', 'order_date')
	search_fields = ('buyer__username', 'product__name')

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
	list_display = ('user', 'product', 'added_date')
	search_fields = ('user__username', 'product__name')

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
	list_display = ('buyer', 'product', 'rating', 'created_date')
	list_filter = ('rating', 'created_date')
	search_fields = ('buyer__username', 'product__name', 'comment')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
	list_display = ('user', 'message', 'is_read', 'created_date')
	list_filter = ('is_read', 'created_date')
	search_fields = ('user__username', 'message')
