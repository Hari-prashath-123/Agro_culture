from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from .forms import LoginForm, RegistrationForm
from .models import UserProfile, Product, Order
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

	return render(request, 'admin_summary.html', {
		'total_transactions': total_transactions,
		'farmers': farmers,
		'buyers': buyers,
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
	products = Product.objects.all()
	if query:
		products = products.filter(Q(name__icontains=query) | Q(category__icontains=query))

	if request.method == 'POST' and 'buy_product_id' in request.POST:
		product_id = request.POST.get('buy_product_id')
		quantity = int(request.POST.get('quantity', 1))
		try:
			product = Product.objects.get(id=product_id)
			if product.quantity >= quantity:
				product.quantity -= quantity
				product.save()
				Order.objects.create(buyer=user, product=product, quantity=quantity)
				messages.success(request, f'Purchased {quantity} of {product.name}!')
			else:
				messages.error(request, 'Not enough stock available.')
		except Product.DoesNotExist:
			messages.error(request, 'Product not found.')
		return redirect('buyer_dashboard')

	return render(request, 'buyer_dashboard.html', {
		'products': products,
		'query': query,
	})

@login_required
def farmer_dashboard(request):
	user = request.user
	# Ensure only farmers can access
	if not hasattr(user, 'userprofile') or user.userprofile.role != 'Farmer':
		messages.error(request, 'Access denied. Only Farmers can view this page.')
		return redirect('login')

	products = Product.objects.filter(farmer=user)
	total_sales = {}
	for product in products:
		total_sales[product.id] = Order.objects.filter(product=product).aggregate(Sum('quantity'))['quantity__sum'] or 0

	if request.method == 'POST':
		form = ProductForm(request.POST, request.FILES)
		if form.is_valid():
			new_product = form.save(commit=False)
			new_product.farmer = user
			new_product.save()
			messages.success(request, 'Product added successfully!')
			return redirect('farmer_dashboard')
	else:
		form = ProductForm()

	return render(request, 'farmer_dashboard.html', {
		'products': products,
		'form': form,
		'total_sales': total_sales,
	})

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
