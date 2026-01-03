from django.contrib import admin
from .models import Product, Order, UserProfile

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
	list_display = ('name', 'category', 'price', 'quantity', 'farmer')
	search_fields = ('name', 'category', 'farmer__username')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
	list_display = ('id', 'buyer', 'product', 'quantity', 'order_date')
	search_fields = ('buyer__username', 'product__name')
