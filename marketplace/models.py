
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
	name = models.CharField(max_length=100)
	category = models.CharField(max_length=50)
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
	buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
	product = models.ForeignKey(Product, on_delete=models.CASCADE)
	quantity = models.PositiveIntegerField()
	order_date = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"Order #{self.id} by {self.buyer.username}"
