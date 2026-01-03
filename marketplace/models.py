
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class UserProfile(models.Model):
	ROLE_CHOICES = [
		('Farmer', 'Farmer'),
		('Buyer', 'Buyer'),
		('Admin', 'Admin'),
	]
	user = models.OneToOneField(User, on_delete=models.CASCADE)
	role = models.CharField(max_length=10, choices=ROLE_CHOICES)

	def __str__(self):
		return f"{self.user.username} ({self.role})"

def validate_farmer(user):
	if not hasattr(user, 'userprofile') or user.userprofile.role != 'Farmer':
		raise ValidationError('User must have Farmer role to be linked to a Product.')

class Product(models.Model):
	CATEGORY_CHOICES = [
		('Vegetables - Leafy', 'Vegetables - Leafy'),
		('Vegetables - Root', 'Vegetables - Root'),
		('Vegetables - Marrow', 'Vegetables - Marrow'),
		('Fruits - Seasonal', 'Fruits - Seasonal'),
		('Fruits - Tropical', 'Fruits - Tropical'),
		('Fruits - Berries', 'Fruits - Berries'),
		('Grains & Cereals - Rice', 'Grains & Cereals - Rice'),
		('Grains & Cereals - Wheat', 'Grains & Cereals - Wheat'),
		('Grains & Cereals - Corn', 'Grains & Cereals - Corn'),
		('Pulses & Legumes - Lentils', 'Pulses & Legumes - Lentils'),
		('Pulses & Legumes - Beans', 'Pulses & Legumes - Beans'),
		('Pulses & Legumes - Peas', 'Pulses & Legumes - Peas'),
		('Dairy Products - Milk', 'Dairy Products - Milk'),
		('Dairy Products - Butter', 'Dairy Products - Butter'),
		('Dairy Products - Cheese', 'Dairy Products - Cheese'),
		('Livestock - Poultry', 'Livestock - Poultry'),
		('Livestock - Cattle', 'Livestock - Cattle'),
		('Livestock - Sheep', 'Livestock - Sheep'),
		('Spices & Herbs', 'Spices & Herbs'),
	]
	
	name = models.CharField(max_length=100)
	category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
	price = models.DecimalField(max_digits=10, decimal_places=2)
	quantity = models.PositiveIntegerField()
	image = models.ImageField(upload_to='product_images/', blank=True, null=True)
	farmer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products', validators=[validate_farmer])

	def save(self, *args, **kwargs):
		validate_farmer(self.farmer)
		super().save(*args, **kwargs)

	def __str__(self):
		return self.name

class Order(models.Model):
	STATUS_CHOICES = [
		('Pending', 'Pending'),
		('Shipped', 'Shipped'),
		('Delivered', 'Delivered'),
	]
	buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
	product = models.ForeignKey(Product, on_delete=models.CASCADE)
	quantity = models.PositiveIntegerField()
	order_date = models.DateTimeField(auto_now_add=True)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

	def __str__(self):
		return f"Order #{self.id} by {self.buyer.username}"

class Wishlist(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist')
	product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlisted_by')
	added_date = models.DateTimeField(auto_now_add=True)

	class Meta:
		unique_together = ('user', 'product')

	def __str__(self):
		return f"{self.user.username} - {self.product.name}"

class Review(models.Model):
	STAR_CHOICES = [
		(1, '1 Star'),
		(2, '2 Stars'),
		(3, '3 Stars'),
		(4, '4 Stars'),
		(5, '5 Stars'),
	]
	buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
	product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
	rating = models.IntegerField(choices=STAR_CHOICES)
	comment = models.TextField(blank=True, null=True)
	created_date = models.DateTimeField(auto_now_add=True)

	class Meta:
		unique_together = ('buyer', 'product')

	def __str__(self):
		return f"{self.buyer.username} - {self.product.name} ({self.rating} stars)"

class Notification(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
	message = models.TextField()
	order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
	is_read = models.BooleanField(default=False)
	created_date = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_date']

	def __str__(self):
		return f"Notification for {self.user.username} - {'Read' if self.is_read else 'Unread'}"

class Cart(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart_items')
	product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='in_carts')
	quantity = models.PositiveIntegerField(default=1)
	added_date = models.DateTimeField(auto_now_add=True)

	class Meta:
		unique_together = ('user', 'product')

	def __str__(self):
		return f"{self.user.username} - {self.product.name} ({self.quantity})"

	def get_total_price(self):
		return self.product.price * self.quantity
