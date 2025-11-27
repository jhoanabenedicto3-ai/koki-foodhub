from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.http import require_http_methods

from .models import Product, InventoryItem, Sale
from .forms import ProductForm, InventoryForm, SaleForm
from .services.forecasting import moving_average_forecast
from .auth import group_required  # new: role guard

def signup(request):
    """User registration view"""
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')
        
        # Validation
        if not username or not email or not password:
            messages.error(request, 'All fields are required')
            return render(request, 'pages/signup.html')
        
        if password != password_confirm:
            messages.error(request, 'Passwords do not match')
            return render(request, 'pages/signup.html')
        
        if len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters')
            return render(request, 'pages/signup.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return render(request, 'pages/signup.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
            return render(request, 'pages/signup.html')
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        messages.success(request, 'Account created successfully! Please login.')
        return redirect('login')
    
    return render(request, 'pages/signup.html')

@login_required
def profile(request):
    return render(request, "pages/profile.html", {})

# Dashboard: any authenticated user
@login_required
def dashboard(request):
    top_products = Sale.objects.values("product__name").annotate(
        total_units=Sum("units_sold"), total_revenue=Sum("revenue")
    ).order_by("-total_units")[:5]

    low_stock = [i for i in InventoryItem.objects.select_related("product").all() if i.is_low_stock()]
    
    # Get all products with inventory info
    all_products = Product.objects.all().prefetch_related('inventory_items')
    products_data = []
    categories_set = set()
    
    for product in all_products:
        inv = product.inventory_items.first() if product.inventory_items.exists() else None
        products_data.append({
            'id': product.id,
            'name': product.name,
            'price': float(product.price),
            'category': product.category,
            'quantity': inv.quantity if inv else 0,
            'is_low_stock': inv.is_low_stock() if inv else False,
            'image': product.image.url if product.image else None
        })
        categories_set.add(product.category)
    
    # Sort categories for consistent display
    categories = sorted([c for c in categories_set if c])
    
    context = {
        "top_products": top_products,
        "low_stock": low_stock,
        "all_products": products_data,
        "categories": categories
    }
    return render(request, "pages/dashboard.html", context)

# Products: Manager only
@group_required("Manager")
def product_list(request):
    products = Product.objects.all()
    return render(request, "pages/product_list.html", {"products": products})

@group_required("Manager")
def product_create(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Product created.")
            return redirect("product_list")
    else:
        form = ProductForm()
    return render(request, "pages/product_form.html", {"form": form, "title": "Create Product"})

@group_required("Manager")
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Product updated.")
            return redirect("product_list")
    else:
        form = ProductForm(instance=product)
    return render(request, "pages/product_form.html", {"form": form, "title": "Edit Product"})

@group_required("Manager")
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        product.delete()
        messages.success(request, "Product deleted.")
        return redirect("product_list")
    return render(request, "pages/product_form.html", {"form": None, "title": "Delete Product", "confirm": True})

# Inventory: Manager only
@group_required("Manager")
def inventory_list(request):
    items = InventoryItem.objects.select_related("product").all()
    return render(request, "pages/inventory_list.html", {"items": items})

@group_required("Manager")
def inventory_create(request):
    if request.method == "POST":
        form = InventoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Inventory item created.")
            return redirect("inventory_list")
    else:
        form = InventoryForm()
    return render(request, "pages/inventory_form.html", {"form": form, "title": "Create Inventory Item"})

@group_required("Manager")
def inventory_update(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    if request.method == "POST":
        form = InventoryForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, "Inventory item updated.")
            return redirect("inventory_list")
    else:
        form = InventoryForm(instance=item)
    return render(request, "pages/inventory_form.html", {"form": form, "title": "Edit Inventory Item"})

@group_required("Manager")
def inventory_delete(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    if request.method == "POST":
        item.delete()
        messages.success(request, "Inventory item deleted.")
        return redirect("inventory_list")
    return render(request, "pages/inventory_form.html", {"form": None, "title": "Delete Inventory Item", "confirm": True})

# Sales: Cashier or Manager
@group_required("Cashier", "Manager")
def sale_list(request):
    sales = Sale.objects.select_related("product").all()
    return render(request, "pages/sale_list.html", {"sales": sales})

@group_required("Cashier", "Manager")
def sale_create(request):
    if request.method == "POST":
        form = SaleForm(request.POST)
        if form.is_valid():
            sale = form.save()
            # decrement inventory if exists
            try:
                inv = InventoryItem.objects.get(product=sale.product)
                inv.quantity = max(inv.quantity - sale.units_sold, 0)
                inv.save()
            except InventoryItem.DoesNotExist:
                pass
            messages.success(request, "Sale recorded.")
            return redirect("sale_list")
    else:
        form = SaleForm()
    return render(request, "pages/sale_form.html", {"form": form, "title": "Record Sale"})

@group_required("Cashier", "Manager")
def sale_update(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if request.method == "POST":
        form = SaleForm(request.POST, instance=sale)
        if form.is_valid():
            form.save()
            messages.success(request, "Sale updated.")
            return redirect("sale_list")
    else:
        form = SaleForm(instance=sale)
    return render(request, "pages/sale_form.html", {"form": form, "title": "Edit Sale"})

@group_required("Cashier", "Manager")
def sale_delete(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if request.method == "POST":
        sale.delete()
        messages.success(request, "Sale deleted.")
        return redirect("sale_list")
    return render(request, "pages/sale_form.html", {"form": None, "title": "Delete Sale", "confirm": True})

# Sales Dashboard: any authenticated user
@login_required
def sales_dashboard(request):
    return render(request, "pages/sales_dashboard.html")

# Forecast: Manager only
@group_required("Manager")
def forecast_view(request):
    from .services.forecasting import get_csv_forecast
    from datetime import datetime, timedelta
    
    # Get CSV-based forecasts (real data)
    csv_data = get_csv_forecast()
    
    # Get database forecasts
    db_results = moving_average_forecast(window=3)
    db_forecasts = db_results.get('db_forecasts', {})
    
    # Prepare data for template
    data = []
    
    # Add CSV forecasts
    for product_name, forecast_info in csv_data.items():
        # Ensure confidence is a percentage (0-100)
        confidence = forecast_info['confidence']
        if confidence < 1:  # If it's still in decimal format (0-1), convert to percentage
            confidence = confidence * 100
        
        data.append({
            "product": product_name,
            "forecast": forecast_info['forecast'],
            "avg": forecast_info['avg'],
            "trend": forecast_info['trend'],
            "confidence": confidence,
            "history": forecast_info['history'],
            "last_7_days": forecast_info['last_7_days'],
            "source": "Real Data (CSV)",
            "is_csv": True
        })
    
    # Calculate analytics
    total_forecasted_units = sum(item['forecast'] for item in data)
    avg_confidence = sum(item['confidence'] for item in data) / len(data) if data else 0
    
    # Calculate next week forecast (7 days)
    next_week_forecast = total_forecasted_units * 7
    
    # Determine peak day (Saturday is typically busier)
    peak_day = "Saturday"
    peak_orders = int(total_forecasted_units * 1.2)  # 20% increase on peak day
    
    # Calculate week-over-week growth
    last_week_total = sum(item['last_7_days'] for item in data)
    growth_percentage = ((next_week_forecast - last_week_total) / last_week_total * 100) if last_week_total > 0 else 0
    
    context = {
        "data": data,
        "total_forecast": next_week_forecast,
        "avg_confidence": avg_confidence,
        "peak_day": peak_day,
        "peak_orders": peak_orders,
        "growth_percentage": growth_percentage,
        "currency": "₱"
    }
    return render(request, "pages/forecast.html", context)
    # Add database forecasts as fallback
    for pid, r in db_forecasts.items():
        try:
            product = Product.objects.get(pk=pid)
            data.append({
                "product": product.name,
                "forecast": r["forecast"],
                "avg": r["avg"],
                "trend": "unknown",
                "confidence": 0,
                "history": r["history"],
                "last_7_days": sum([u for _, u in r["history"][-7:]]),
                "source": "Database",
                "is_csv": False
            })
        except Product.DoesNotExist:
            pass
    return render(request, "pages/forecast.html", {"data": data})

@login_required
def create_sale(request):
    """API endpoint to create a sale transaction"""
    from django.http import JsonResponse
    from django.views.decorators.http import require_http_methods
    import json
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            items = data.get('items', [])
            
            if not items:
                return JsonResponse({'error': 'No items in cart'}, status=400)
            
            # Create sale records for each item
            for item in items:
                product = Product.objects.get(pk=item['id'])
                sale = Sale.objects.create(
                    product=product,
                    units_sold=item['quantity'],
                    revenue=float(item['price']) * item['quantity']
                )
                
                # Update inventory
                inv = product.inventory_items.first()
                if inv:
                    inv.quantity -= item['quantity']
                    inv.save()
            
            return JsonResponse({'success': True, 'message': 'Sale recorded successfully'})
        except Product.DoesNotExist:
            return JsonResponse({'error': 'Product not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)
