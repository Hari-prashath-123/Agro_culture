from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, Avg
from django.http import JsonResponse
from .forms import LoginForm, RegistrationForm
from .models import UserProfile, Product, Order, Wishlist, Review, Notification
from .product_form import ProductForm

@login_required
def admin_summary(request):
	user = request.user
	# Ensure only admins can access
	if not hasattr(user, 'userprofile') or user.userprofile.role != 'Admin':
		messages.error(request, 'Access denied. Only Admins can view this page.')
		return redirect('login')

	total_transactions = Order.objects.count()
	farmers = UserProfile.objects.filter(role='Farmer')
	buyers = UserProfile.objects.filter(role='Buyer')

	# Count products by category
	from django.db.models import Count
	category_counts = dict(Product.objects.values_list('category').annotate(count=Count('id')))

	return render(request, 'admin_summary.html', {
		'total_transactions': total_transactions,
		'farmers': farmers,
		'buyers': buyers,
		'category_counts': category_counts,
	})
from django.db.models import Q

@login_required
def buyer_dashboard(request):
	user = request.user
	# Ensure only buyers can access
	if not hasattr(user, 'userprofile') or user.userprofile.role != 'Buyer':
		messages.error(request, 'Access denied. Only Buyers can view this page.')
		return redirect('login')

	query = request.GET.get('q', '')
	category_filter = request.GET.get('category', '')
	min_price = request.GET.get('min_price', '')
	max_price = request.GET.get('max_price', '')
	
	products = Product.objects.all()
	
	# Apply text search filter
	if query:
		products = products.filter(Q(name__icontains=query) | Q(category__icontains=query))
	
	# Apply category filter
	if category_filter:
		products = products.filter(category=category_filter)
	
	# Apply price range filter
	if min_price:
		try:
			products = products.filter(price__gte=float(min_price))
		except ValueError:
			pass
	if max_price:
		try:
			products = products.filter(price__lte=float(max_price))
		except ValueError:
			pass
	
	# Get user's wishlist product IDs
	wishlist_ids = Wishlist.objects.filter(user=user).values_list('product_id', flat=True)
	
	# Calculate average ratings for products
	product_ratings = {}
	for product in products:
		avg_rating = Review.objects.filter(product=product).aggregate(Avg('rating'))['rating__avg']
		product_ratings[product.id] = round(avg_rating, 1) if avg_rating else 0
	
	# Get products the user has ordered (for review eligibility)
	purchased_product_ids = Order.objects.filter(buyer=user).values_list('product_id', flat=True).distinct()
	
	# Get products the user has already reviewed
	reviewed_product_ids = Review.objects.filter(buyer=user).values_list('product_id', flat=True)

	if request.method == 'POST' and 'buy_product_id' in request.POST:
		product_id = request.POST.get('buy_product_id')
		quantity = int(request.POST.get('quantity', 1))
		try:
			product = Product.objects.get(id=product_id)
			if product.quantity >= quantity:
				product.quantity -= quantity
				product.save()
				order = Order.objects.create(buyer=user, product=product, quantity=quantity)
				
				# Create notification for the farmer
				Notification.objects.create(
					user=product.farmer,
					message=f"{user.username} ordered {quantity} units of {product.name}",
					order=order
				)
				
				messages.success(request, f'Purchased {quantity} of {product.name}!')
			else:
				messages.error(request, 'Not enough stock available.')
		except Product.DoesNotExist:
			messages.error(request, 'Product not found.')
		return redirect('buyer_dashboard')

	return render(request, 'buyer_dashboard.html', {
		'products': products,
		'query': query,
		'category_filter': category_filter,
		'min_price': min_price,
		'max_price': max_price,
		'category_choices': Product.CATEGORY_CHOICES,
		'wishlist_ids': wishlist_ids,
		'product_ratings': product_ratings,
		'purchased_product_ids': purchased_product_ids,
		'reviewed_product_ids': reviewed_product_ids,
	})

# Buyer Order History View
@login_required
def order_history(request):
	user = request.user
	if not hasattr(user, 'userprofile') or user.userprofile.role != 'Buyer':
		messages.error(request, 'Access denied. Only Buyers can view this page.')
		return redirect('login')
	order_history = Order.objects.filter(buyer=user).select_related('product').order_by('-order_date')
	return render(request, 'order_history.html', {'order_history': order_history})


# Farmer Products List View
@login_required
def farmer_products(request):
	user = request.user
	if not hasattr(user, 'userprofile') or user.userprofile.role != 'Farmer':
		messages.error(request, 'Access denied. Only Farmers can view this page.')
		return redirect('login')
	products = Product.objects.filter(farmer=user)
	total_sales = {}
	total_products_sold = 0
	total_revenue = 0
	category_sales = {}
	
	for product in products:
		product_sold = Order.objects.filter(product=product).aggregate(Sum('quantity'))['quantity__sum'] or 0
		total_sales[product.id] = product_sold
		total_products_sold += product_sold
		
		# Calculate revenue for this product
		orders = Order.objects.filter(product=product)
		for order in orders:
			total_revenue += order.quantity * product.price
		
		# Track sales by category
		if product.category not in category_sales:
			category_sales[product.category] = 0
		category_sales[product.category] += product_sold
	
	# Find top selling category
	top_category = max(category_sales, key=category_sales.get) if category_sales else 'N/A'
	
	# Get orders for farmer's products
	orders = Order.objects.filter(product__farmer=user).select_related('product', 'buyer').order_by('-order_date')
	
	return render(request, 'farmer_products.html', {
		'products': products,
		'total_sales': total_sales,
		'total_products_sold': total_products_sold,
		'total_revenue': total_revenue,
		'top_category': top_category,
		'orders': orders,
	})

# Add New Product View
@login_required
def add_product(request):
	user = request.user
	if not hasattr(user, 'userprofile') or user.userprofile.role != 'Farmer':
		messages.error(request, 'Access denied. Only Farmers can view this page.')
		return redirect('login')
	if request.method == 'POST':
		form = ProductForm(request.POST, request.FILES)
		if form.is_valid():
			new_product = form.save(commit=False)
			new_product.farmer = user
			new_product.save()
			messages.success(request, 'Product added successfully!')
			return redirect('farmer_products')
	else:
		form = ProductForm()
	return render(request, 'add_product.html', {'form': form})

def unified_login(request):
	if request.method == 'POST':
		form = LoginForm(request.POST)
		if form.is_valid():
			username = form.cleaned_data['username']
			password = form.cleaned_data['password']
			user = authenticate(request, username=username, password=password)
			if user is not None:
				login(request, user)
				try:
					role = user.userprofile.role
				except UserProfile.DoesNotExist:
					messages.error(request, 'User role not set.')
					return redirect('login')
				if role == 'Farmer':
					return redirect('farmer_dashboard')
				elif role == 'Buyer':
					return redirect('buyer_dashboard')
				elif role == 'Admin':
					return redirect('admin_summary')
				else:
					messages.error(request, 'Invalid role.')
			else:
				messages.error(request, 'Invalid credentials.')
	else:
		form = LoginForm()
	return render(request, 'login.html', {'form': form})

def register(request):
	if request.method == 'POST':
		form = RegistrationForm(request.POST)
		if form.is_valid():
			form.save()
			messages.success(request, 'Registration successful. Please log in.')
			return redirect('login')
	else:
		form = RegistrationForm()
	return render(request, 'register.html', {'form': form})

def home(request):
	if request.user.is_authenticated:
		if hasattr(request.user, 'userprofile'):
			role = request.user.userprofile.role
			if role == 'Farmer':
				return redirect('farmer_dashboard')
			elif role == 'Buyer':
				return redirect('buyer_dashboard')
			elif role == 'Admin':
				return redirect('admin_summary')
	return redirect('login')

def logout_view(request):
	logout(request)
	return redirect('login')

@login_required
def toggle_wishlist(request, product_id):
	if request.method == 'POST':
		user = request.user
		if not hasattr(user, 'userprofile') or user.userprofile.role != 'Buyer':
			return JsonResponse({'success': False, 'message': 'Only buyers can add to wishlist'}, status=403)
		
		try:
			product = Product.objects.get(id=product_id)
			wishlist_item = Wishlist.objects.filter(user=user, product=product).first()
			
			if wishlist_item:
				# Remove from wishlist
				wishlist_item.delete()
				return JsonResponse({'success': True, 'action': 'removed', 'message': 'Removed from wishlist'})
			else:
				# Add to wishlist
				Wishlist.objects.create(user=user, product=product)
				return JsonResponse({'success': True, 'action': 'added', 'message': 'Added to wishlist'})
			
		except Product.DoesNotExist:
			return JsonResponse({'success': False, 'message': 'Product not found'}, status=404)
	
	return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

@login_required
def submit_review(request, product_id):
	if request.method == 'POST':
		user = request.user
		if not hasattr(user, 'userprofile') or user.userprofile.role != 'Buyer':
			return JsonResponse({'success': False, 'message': 'Only buyers can submit reviews'}, status=403)
		
		# Check if user has purchased this product
		has_purchased = Order.objects.filter(buyer=user, product_id=product_id).exists()
		if not has_purchased:
			return JsonResponse({'success': False, 'message': 'You can only review products you have purchased'}, status=403)
		
		try:
			product = Product.objects.get(id=product_id)
			rating = int(request.POST.get('rating', 0))
			comment = request.POST.get('comment', '').strip()
			
			if rating < 1 or rating > 5:
				return JsonResponse({'success': False, 'message': 'Rating must be between 1 and 5'}, status=400)
			
			# Create or update review
			review, created = Review.objects.update_or_create(
				buyer=user,
				product=product,
				defaults={'rating': rating, 'comment': comment}
			)
			
			# Calculate new average rating
			avg_rating = Review.objects.filter(product=product).aggregate(Avg('rating'))['rating__avg']
			avg_rating = round(avg_rating, 1) if avg_rating else 0
			
			action = 'submitted' if created else 'updated'
			return JsonResponse({
				'success': True,
				'action': action,
				'message': f'Review {action} successfully!',
				'avg_rating': avg_rating
			})
			
		except Product.DoesNotExist:
			return JsonResponse({'success': False, 'message': 'Product not found'}, status=404)
		except ValueError:
			return JsonResponse({'success': False, 'message': 'Invalid rating value'}, status=400)
	
	return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

@login_required
def notifications(request):
	user = request.user
	notifications = Notification.objects.filter(user=user)
	
	# Mark all as read
	if request.method == 'POST':
		notifications.update(is_read=True)
		return redirect('notifications')
	
	# Determine user role for back button
	user_role = user.userprofile.role if hasattr(user, 'userprofile') else None
	
	return render(request, 'notifications.html', {
		'notifications': notifications,
		'user_role': user_role
	})

@login_required
def get_notification_count(request):
	user = request.user
	unread_count = Notification.objects.filter(user=user, is_read=False).count()
	return JsonResponse({'unread_count': unread_count})

@login_required
def update_order_status(request, order_id):
	if request.method == 'POST':
		user = request.user
		if not hasattr(user, 'userprofile') or user.userprofile.role != 'Farmer':
			return JsonResponse({'success': False, 'message': 'Only farmers can update order status'}, status=403)
		
		try:
			order = Order.objects.get(id=order_id, product__farmer=user)
			new_status = request.POST.get('status')
			
			if new_status in dict(Order.STATUS_CHOICES):
				order.status = new_status
				order.save()
				
				# Create notification for the buyer
				Notification.objects.create(
					user=order.buyer,
					message=f"Your order #{order.id} for {order.product.name} is now {new_status}",
					order=order
				)
				
				return JsonResponse({'success': True, 'status': new_status, 'message': 'Status updated successfully'})
			else:
				return JsonResponse({'success': False, 'message': 'Invalid status'}, status=400)
			
		except Order.DoesNotExist:
			return JsonResponse({'success': False, 'message': 'Order not found or access denied'}, status=404)
	
	return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)
